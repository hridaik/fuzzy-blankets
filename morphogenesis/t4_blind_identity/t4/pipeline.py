"""Online per-run processing (stage 1): detection, tracking, events, body frames, descriptors.
Strictly causal: frame k uses only frames <= k."""
import json, os
import numpy as np
from . import io, o3
from .celltrack import CellTracker
from .orgtrack import OrganismTracker
from .describe import describe
from .geom import body_frame


def load_geometry():
    return json.load(open(os.path.join(io.ROOT, 'calibration', 'geometry.json')))


def _org_record(o, xy, lev, ch, r_coh):
    idx = o['idx']
    bf = o['frame']
    desc = describe(xy[idx], lev[idx], ch, bf, r_coh)
    return dict(org=int(o['org']), members=o['members'], n=int(len(idx)), centroid=[float(v) for v in bf['centroid']],
                e1=[float(v) for v in bf['e1']], axis_conf=float(bf.get('axis_conf', 0)), sign_conf=float(bf.get('sign_conf', 0)),
                sign_src=bf.get('sign_src', ''), unresolved=bool(o['unresolved']), parent=o['parent'], desc=desc)


def process_points(run, level, geo, track_cells=None):
    ch = io.CHANNELS[level]
    frames = io.point_frames(run, level)
    ot = OrganismTracker(ch, geo['r_link'], geo['m_min'], geo['margin'], geo['r_hold'])
    ct = CellTracker(ch) if level == 'O2' else None
    out = []
    for k, f in enumerate(frames):
        if level == 'O1':
            ids = f['ids']; tinfo = {}
        else:
            ids, tinfo = ct.step(f['xy'], f['lev'])
        orgs, ev = ot.step(f['t'], f['xy'], f['lev'], ids)
        recs = [_org_record(o, f['xy'], f['lev'], ch, geo['r_coh']) for o in orgs]
        in_org = sum(len(o['idx']) for o in orgs)
        out.append(dict(k=k, t=f['t'], n_points=int(len(f['xy'])), n_free=int(len(f['xy']) - in_org), orgs=recs,
                        events=ev, track=tinfo.get('reg', ''), cells=dict(xy=f['xy'].round(3).tolist(), ids=[int(i) for i in ids])))
    return dict(run=run, level=level, ch=ch, frames=out)


def _field_sign(bf, img, fov, reg_pix, fp, geo, prev_e1):
    """Orientation sign at O3 from an observable asymmetry between two fluorescence fields: the displacement
    of the c6-field centroid from the c2-field centroid along the candidate axis. Its sign convention
    (e1 points from the c2-heavy end to the c6-heavy end) is the same as the sign defined at O1/O2 by the c6 gradient,
    verified on development calibration dishes. conf = 1-exp(-(|S|/S0)^2)."""
    from . import segment
    X, Y = segment.grid(fov)
    P = np.c_[X.ravel(), Y.ravel()][reg_pix]

    def cent(c):
        w = np.clip(img[c].ravel()[reg_pix].astype(float) - float(np.mean(img[c][np.hypot(X, Y) > 0.75 * fov])), 0, None)
        return (P * w[:, None]).sum(0) / max(w.sum(), 1e-9)
    # channel 0 is c6, channel 1 is c2 in both O3 variants
    S = float((cent(0) - cent(1)) @ bf['e1'])
    conf = float(1 - np.exp(-(abs(S) / geo['o3_sign_S0']) ** 2))
    e1 = bf['e1'] if S >= 0 else -bf['e1']
    src = 'field_asym'
    if conf < 0.9 and prev_e1 is not None:
        if e1 @ prev_e1 < 0:
            e1 = -e1
        src = 'continuity'
    bf = dict(bf); bf['e1'] = e1; bf['e2'] = np.array([-e1[1], e1[0]]); bf['sign_conf'] = conf; bf['sign_src'] = src
    bf['S'] = S
    return bf


def process_images(run, level, geo, fov):
    ch = io.CHANNELS[level]
    ts, imgs = io.image_frames(run, level)
    px = 2 * fov / 64
    m_px = max(3, int(round(geo['m_min'] * 1.0 / px ** 2)))
    ot = OrganismTracker(ch, 1.0, m_px, geo['margin'], None)
    out = []
    prev_n = {}
    for k in range(len(ts)):
        fp = o3.frame_points(imgs[k], fov, geo)
        orgs, ev = ot.step(float(ts[k]), fp['xy'], fp['lev'], fp['ids'], lab=fp['lab'], compute_frame=False)
        recs = []
        # replace pixel-level cell events (meaningless at field level) by mass-based arrival/loss
        ev = [e for e in ev if e['type'] not in ('EXTRUSION', 'ARRIVAL', 'LOSS')]
        regs = o3.regions(64, [fp['ids'][o['idx']] for o in orgs], fov, geo) if orgs else []
        for o, pix in zip(orgs, regs):
            cen, amps, n, mass = o3.pseudo_cells(imgs[k], fov, pix, geo)
            bf = body_frame(cen, amps, [], ot.prev_e1.get(o['org']))
            bf = _field_sign(bf, imgs[k], fov, pix, fp, geo, ot.prev_e1.get(o['org']))
            ot.prev_e1[o['org']] = bf['e1']
            desc = describe(cen, amps, ch, bf, geo['r_coh'])
            desc['n'] = float(mass / geo['mass_per_cell'])
            oid = int(o['org'])
            if oid in prev_n and abs(desc['n'] - prev_n[oid]) >= 1.5:
                ev.append(dict(type='ARRIVAL' if desc['n'] > prev_n[oid] else 'LOSS', org=oid, t=float(ts[k]), k=k,
                               cell=-1, mass_based=True, dn=float(desc['n'] - prev_n[oid])))
            prev_n[oid] = desc['n']
            recs.append(dict(org=oid, members=[], n_pixels=int(len(o['idx'])), n=n, centroid=[float(v) for v in bf['centroid']],
                             e1=[float(v) for v in bf['e1']], axis_conf=float(bf['axis_conf']), sign_conf=float(bf['sign_conf']),
                             sign_src=bf['sign_src'], unresolved=bool(o['unresolved']), parent=o['parent'], desc=desc,
                             _pix=[int(v) for v in pix], _pseudo=dict(xy=cen.round(3).tolist(), lev=amps.round(3).tolist())))
        out.append(dict(k=k, t=float(ts[k]), n_free=0, orgs=recs, events=ev, track='', cells=None))
    return dict(run=run, level=level, ch=ch, frames=out)


def process(run, level, geo, fov):
    if level in ('O1', 'O2'):
        return process_points(run, level, geo)
    return process_images(run, level, geo, fov)
