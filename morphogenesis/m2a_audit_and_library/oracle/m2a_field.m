function c = m2a_field(x,s,y)
% identical to SPM morphogenesis(): ligand concentration sensed at y (default x)
if nargin < 3; y = x; end
n = size(y,2); m = size(s,1); c = zeros(m,n);
for i = 1:n
    for j = 1:size(x,2)
        d = y(:,i) - x(:,j); d = sqrt(d'*d);
        c(:,i) = c(:,i) + exp(-d).*s(:,j);
    end
end
end
