function run_a5_function_check(outpath)
% A5: evaluate Octave's Gg and Mg on 20 random identical inputs and save
% inputs+outputs for a Python-side comparison against model.py.
if nargin < 1; outpath = 'data/oracle_traces/a5_function_check.mat'; end
addpath('../m0b_reference_port/sources/spm12');
addpath('../m0b_reference_port/sources/spm12/toolbox/DEM');
addpath('../m0b_reference_port/oracle');

% rebuild P (template) exactly as dem_setup does, L=2
T = [0 0 2 0 0 0 0 0 0 0 0;
     0 0 0 0 1 0 0 0 0 0 0;
     2 0 0 0 0 0 4 0 4 0 3;
     0 0 0 0 1 0 0 0 0 0 0;
     0 0 2 0 0 0 0 0 0 0 0;
     0 0 0 0 0 0 0 0 0 0 0];
p(:,:,1) = T > 0;
p(:,:,2) = T == 2 | T == 1;
p(:,:,3) = T == 3 | T == 1;
p(:,:,4) = T == 4;
[y,x] = find(p(:,:,1));
P.x   = spm_detrend([x(:) y(:)])'/2;
n = size(P.x,2); m = size(p,3);
j = find(p(:,:,1));
for i = 1:m
    s = p(:,:,i);
    P.s(i,:) = s(j);
end
P.s = double(P.s);
P.c = dem_morphogenesis_field(P.x,P.s);

rand('seed', 42); randn('seed', 42);
n_tests = 20;
v_tests  = cell(n_tests,1);
a_tests  = cell(n_tests,1);
t_tests  = zeros(n_tests,1);
Mg_out   = cell(n_tests,1);
Gg_out   = cell(n_tests,1);

for k = 1:n_tests
    v = randn(n,n) * (0.2 + 0.5*rand());
    t_tests(k) = rand();   % random t in (0,1)
    global t
    t = t_tests(k);
    g = dem_morphogenesis_Mg([], v, P);
    a.x = randn(2,n)*2;
    a.s = rand(4,n);
    gg = dem_morphogenesis_Gg([], [], a, a);

    v_tests{k} = v;
    a_tests{k} = a;
    Mg_out{k} = g;
    Gg_out{k} = gg;
end

save('-v7', outpath, 'v_tests', 'a_tests', 't_tests', 'Mg_out', 'Gg_out', ...
     'n', 'm', 'P');
fprintf('saved %s\n', outpath);
end
