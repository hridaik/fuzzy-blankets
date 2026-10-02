function p = m2a_pulse(bin, onset, w)
% Raised-cosine bump of total width w bins, 0 -> 1 (at onset+w/2) -> 0.
x = (bin - onset)/w;
if x <= 0 || x >= 1; p = 0; else; p = 0.5*(1 - cos(2*pi*x)); end
end
