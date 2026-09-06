% Cross-language validation harness for stage6_flock (Part A4).
% Run with: octave --no-gui run_fixture.m   (from this directory)
% Requires the verbatim upstream files on the path: addpath('../../../upstream')
% This harness only exercises getMarkovBlanketOfFlock.m (part 2 of the fixture,
% cross_language_fixture.json) since that function is self-contained and does
% not require the full active-inference MDP toolbox that
% active_inference_bird_control.m depends on (part 1 requires SPM12, not
% included here and not verified to be installable in this environment --
% documented as a further, separate gap).
addpath('../../../upstream');
fixture = jsondecode(fileread('cross_language_fixture.json'));
p2 = fixture.part2_fiedler_pipeline;
z_window = p2.z_window;  % (TW, nn), 0-based headings as computed by Python

% getMarkovBlanketOfFlock expects 1-based bird headings starting at 1, and a
% (nt, nn) `sts`-like matrix; the Python fixture already stores 0-based
% headings, so add 1 before calling the upstream function if it assumes
% 1-based category labels (check getMarkovBlanketOfFlock.m's own indexing --
% it operates on equality z_i(t)==z_j(t), which is invariant to a uniform
% +1 shift, so either convention gives the identical adjacency A).
tsign = 1; TW = p2.TW;
[fiedler_vec, A, core1_nodes, core2_nodes, boundary_nodes] = ...
    getMarkovBlanketOfFlock(z_window, tsign, TW);

fprintf('Octave adjacency matches Python (expected all zeros):\n');
disp(A - cell2mat(p2.expected_adjacency));
fprintf('Octave core1_nodes (1-based): '); disp(core1_nodes);
fprintf('Python expected_core1_nodes_0based (+1 for comparison): ');
disp(p2.expected_core1_nodes_0based + 1);
