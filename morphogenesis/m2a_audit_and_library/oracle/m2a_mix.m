function m2a_mix(fa, fb, lam, fout)
% state interpolation for D5 edge tracking: cont_out(fout) = (1-lam)*cont_out(fa) + lam*cont_out(fb); b_end from fa (must match fb)
A = load(fa); B = load(fb);
cont_out = mixs(A.cont_out, B.cont_out, lam);
b_end = A.b_end; %#ok<NASGU>
save('-v6', fout, 'cont_out', 'b_end');
end
function c = mixs(a, b, lam)
if isstruct(a)
    c = a;
    for f = fieldnames(a)'; c.(f{1}) = mixs(a.(f{1}), b.(f{1}), lam); end
elseif iscell(a)
    c = cell(size(a)); for k = 1:numel(a); c{k} = mixs(a{k}, b{k}, lam); end
elseif isnumeric(a)
    c = (1-lam)*a + lam*b;
else
    c = a;
end
end
