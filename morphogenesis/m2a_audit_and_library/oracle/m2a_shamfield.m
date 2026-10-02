function d = m2a_shamfield(x1, x2, freqs, phases, scale)
% identical to M1's sham_field: sum of K cosines, RMS-normalised to `scale`
K = size(freqs,1); d = 0;
for k = 1:K; d = d + cos(2*pi*(freqs(k,1)*x1 + freqs(k,2)*x2) + phases(k)); end
d = scale * d / sqrt(K/2);
end
