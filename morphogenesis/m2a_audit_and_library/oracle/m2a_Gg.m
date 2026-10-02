function g = m2a_Gg(x,v,a,P)
% generative PROCESS mapping (identical to SPM Gg when no events/modes are set).
% M2A.events: struct array with fields type ('pos'|'sec'|'gain'), cells, ch, amp, onset, w
%   pos : g.x(ch,cells) += amp*pulse         (ch=1,2: x,y)   [offset in the position channel]
%   sec : extra ligand ch emitted into the FIELD by cells: s_field(ch,cells) += amp*pulse
%   gain: g.c(ch,cells) *= (1 + amp*pulse)   (extracellular sensitivity to ligand ch)
global t
global M2A
[s, bin] = m2a_ramp(t);
a = spm_unvec(a,P);
g.x(1,:) = a.x(1,:); g.x(2,:) = a.x(2,:); g.s = a.s;
sf = a.s;
ev = []; if ~isempty(M2A) && isfield(M2A,'events'); ev = M2A.events; end
if ~isempty(t) && ~isempty(ev)
    for e = 1:numel(ev)
        switch ev(e).type
            case 'pos';  pu = m2a_pulse(bin, ev(e).onset, ev(e).w) * ev(e).amp;
                         if pu ~= 0; g.x(ev(e).ch, ev(e).cells) = g.x(ev(e).ch, ev(e).cells) + pu; end
            case 'sec';  pu = m2a_pulse(bin, ev(e).onset, ev(e).w) * ev(e).amp;
                         if pu ~= 0; sf(ev(e).ch, ev(e).cells) = sf(ev(e).ch, ev(e).cells) + pu; end
            case 'kuch'  % Kuchling-type distortion of the sensed long-axis position: x1 -> sign*x1^2 (ramped on/off)
                r = m2a_onoff(bin, ev(e).onset, ev(e).off, ev(e).w);
                if r ~= 0
                    for c = ev(e).cells(:)'
                        g.x(1,c) = (1-r)*a.x(1,c) + r*ev(e).sign*(a.x(1,c)^2);
                    end
                end
            case 'kuche'  % quasi-static family: g.x(1,c) = (1-L) x + L*sign*x^2, L stepped smoothly from amp0 to amp (raised cosine over w bins from onset)
                r = m2a_onoff(bin, ev(e).onset, [], ev(e).w); Lv = ev(e).amp0 + (ev(e).amp - ev(e).amp0)*r;
                for c = ev(e).cells(:)'
                    g.x(1,c) = (1-Lv)*a.x(1,c) + Lv*ev(e).sign*(a.x(1,c)^2);
                end
            case 'fscale'  % Friston-2015-Fig.5-style channel scaling (m0c declared interpretation): ch 1=position_all 2=position_row1 3=secretion
                r = m2a_onoff(bin, ev(e).onset, ev(e).off, ev(e).w);
                if r ~= 0
                    f = 1 + r*(ev(e).amp - 1);
                    switch ev(e).ch
                        case 1; g.x(:, ev(e).cells) = f*g.x(:, ev(e).cells);
                        case 2; g.x(1, ev(e).cells) = f*g.x(1, ev(e).cells);
                        case 3; g.s(:, ev(e).cells) = f*g.s(:, ev(e).cells);
                    end
                end
            case 'sham'  % random smooth displacement field of the sensed position (random Fourier features)
                r = m2a_onoff(bin, ev(e).onset, ev(e).off, ev(e).w);
                if r ~= 0
                    for c = ev(e).cells(:)'
                        dx = m2a_shamfield(a.x(1,c), a.x(2,c), ev(e).freqs, ev(e).phx, ev(e).amp);
                        dy = m2a_shamfield(a.x(1,c), a.x(2,c), ev(e).freqs, ev(e).phy, ev(e).amp);
                        g.x(1,c) = (1-r)*a.x(1,c) + r*(a.x(1,c) + dx);
                        g.x(2,c) = (1-r)*a.x(2,c) + r*(a.x(2,c) + dy);
                    end
                end
        end
    end
end
g.c = s*m2a_field(a.x, sf);
if ~isempty(t) && ~isempty(ev)
    for e = 1:numel(ev)
        if strcmp(ev(e).type,'gain')
            pu = m2a_pulse(bin, ev(e).onset, ev(e).w) * ev(e).amp;
            if pu ~= 0; g.c(ev(e).ch, ev(e).cells) = g.c(ev(e).ch, ev(e).cells) * (1 + pu); end
        end
    end
end
end
