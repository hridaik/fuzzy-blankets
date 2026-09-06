function C = getMarkovBlanketOfFlock(sts,tsign,TW,refclust)

% Author: Domenico Maisto

% INPUT: sts encodes the heading directions, tsign is the initial timestep
% of the time window of length TW, and refclust is the flock for which we 
% want to find the Markov blanket.

% OUTPUT: a figure where a markov blanket of a preminent flock is
% represented. The colors indicate the role of the cells: blue for 
% the internal, cyan for the external, red for active, and magenta 
% for sensory. 

if nargin<3
    TW=5;
end

if nargin<4
    refclust=[];
end

rng('default'); 

try
    st = cellfun(@(x)[x{:}],sts{:},'UniformOutput',false);
    nn = size(st{:},1);
catch
    st=sts;
    nn = size(st,1);
end

l=sqrt(nn);

A = zeros(nn);
% 
for t=tsign:tsign+TW-1
    for i=1:nn   
        for j=i:nn
            try
                if st{:}(i,t)==st{:}(j,t) 
                    A(i,j) = A(i,j)+1;
                    A(j,i) = A(i,j);
                end
            catch
                if st(i,t)==st(j,t) 
                    A(i,j) = A(i,j)+1;
                    A(j,i) = A(i,j);
                end                    
            end
        end
    end
end

% normalized Laplacian
D = diag(sum(A, 2));
L = D - A;

% Compute eigenvectors and eigenvalues
[eigenvectors, eigenvalues] = eig(full(L));
eigenvals = diag(eigenvalues);

% Detect Fiedler vector
[~, idx] = sort(eigenvals);
fiedler_vector = eigenvectors(:, idx(2)); 

% Normalize Fiedler vector
fiedler_norm = fiedler_vector / max(abs(fiedler_vector));

[core1_nodes,core2_nodes,boundary_nodes,conn_cluster1,conn_cluster2] = information_flow_interpretation(A,fiedler_norm);

mymap = [0 0 1      % internals
         0 1 1      % external
         1 0 0      % active
         1 0 1];    % sensory

if ~isempty(refclust)
    if sum(ismember(core1_nodes,refclust))<sum(ismember(core2_nodes,refclust))
        tmp=core1_nodes;
        core1_nodes=core2_nodes;
        core2_nodes=tmp;

        tmp=conn_cluster1;
        conn_cluster1=conn_cluster2;
        conn_cluster2=tmp;
    end
end

C=zeros(nn,1);
C(core1_nodes)=0;
C(core2_nodes)=1;
for i=1:length(boundary_nodes)
    switch conn_cluster1(i)>=conn_cluster2(i)
        case 1
            C(boundary_nodes(i)) = 2;
        case 0
            C(boundary_nodes(i)) = 3;
    end
end


figure
xrange = [1 l]; 
yrange = [1 l];
dx = diff(xrange)/(l-1);
dy = diff(yrange)/(l-1);
xg = linspace(xrange(1)-dx/2,xrange(2)+dx/2,l+1);
yg = linspace(yrange(1)-dy/2,yrange(2)+dy/2,l+1);

imagesc(xrange,yrange,reshape(C,l,l));  
colormap(mymap) 
hold on
hm=mesh(xg,yg,zeros([l,l]+1));
hm.FaceColor = 'none';
hm.EdgeColor = 'k';


cbh = colorbar ; 

cbh_range=[0,3];
dr = diff(cbh_range)/3;
rg = linspace(cbh_range(1)+dr/2,cbh_range(2)-dr/2,4);
cbh.Ticks = rg; 
cbh.TickLabels = {'internal','external','active','sensory'};   
cbh.FontSize = 18;

end

%%
function [core1_nodes,core2_nodes,boundary_nodes,conn_cluster1,conn_cluster2]=information_flow_interpretation(A, y_2)
    % Fiedler vector as information flow
    
    core1_nodes = find(y_2 > quantile(y_2, 0.8));  % Top 20% positive
    core2_nodes = find(y_2 < quantile(y_2, 0.2));  % Bottom 20% negative
    boundary_nodes = find(abs(y_2) < 0.05);        % Borders


    % Assess strength connection
    conn_cluster1 = zeros(length(boundary_nodes),1);
    conn_cluster2 = zeros(length(boundary_nodes),1);

    for i = 1:length(boundary_nodes) 
        node = boundary_nodes(i);
        conn_cluster1(i) = sum(A(node, core1_nodes));
        conn_cluster2(i) = sum(A(node, core2_nodes));
        total_conn = sum(A(node, :));
        
        fprintf('Nodo %d: Connections = [C1:%d, C2:%d, Tot:%d]\n', ...
                node, conn_cluster1, conn_cluster2, total_conn);
    end
end

