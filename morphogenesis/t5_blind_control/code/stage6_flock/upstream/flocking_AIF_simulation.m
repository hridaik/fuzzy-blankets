function [sts,std,Phi,H] = flocking_AIF_simulation(param)

% Author: Domenico Maisto
%--------------------------------------------------------------------------

clear global

rng('default') 


try                          % number of epochs
    ne = param.ne;
catch
    ne = 1;
end
try                        % number of trials 
    nb = param.nb;
catch
    nb = 1; 
end
try                       % number of time steps
    nt = param.nt;
catch
    nt = 60;
end
try                          % number of bird
    try
       nn = numel(param.conf);
    catch
        nn = param.nn;
    end
catch
    nn = 100;                % linearly numbered by columns in a grid deployment
end
try
    nh = param.nh;           % size of neighbourhood
catch
    nh = 8;
end
try
    nu = param.nu;           % number of actions; it corresponds to the nuber of states of each bird
catch
    nu = 4;
end
%
try
    conf=param.conf;
catch
    conf=[];
end
%
try
    vm = param.algnmt;      % velocity matching
catch
    vm = 4;
end
try
    ca = param.clsavd;      % collision avoidance 
catch
    ca = 2; 
end
try
    fc = param.flckcntr;    % flock centering
catch
    fc = 1; 
end
%
try
    precAbird = param.precAnotInDanger;
catch
    precAbird = 1;
end
try
    precApred = param.precAinDanger;
catch
    precApred = 1;
end
try
    precB = param.precisionB;
catch
    precB = 15;
end
try
    precC = param.precisionC;
catch
    precC = 3;
end
try
    pu = param.pu;           % event probabilities of a categorical
                             % distribution controlling the state
                             % initialization of the birds.
    if numel(pu) ~= nu
        error('The vector param.pu needs to have the same size of the number of actions param.nu');
    end
catch
    pu = ones(nu,1)/nu;
end
try
    asynch=param.asynch;
    try
        asynchUpdtPercent = param.asynchUpdtPercent;
    catch
        asynchUpdtPercent = 70;
    end
catch 
    asynch=0;
end
try
    predators = param.predators;    % Predator map
    yesFigWithPredators = 1;
catch
    create_containers = @(n)arrayfun(@(x)containers.Map(), 1:nt, 'UniformOutput', false);
    predators = create_containers(nn); 
    yesFigWithPredators = 0;
end

try
    T_refract = param.T_refract;    % Refractory period
catch
    T_refract = 10;
end

try
    tau = param.tau;                % mean life of the stressed state decay
catch
    tau = 2;
end


% The data structure cointaining the MDP
MDP = defineMDP(ne,nb,nt,nn);


Phi = cell(ne,1); Phi(:) = {cell(nb,1)};
for e=1:ne, Phi{e,1}(:) = {cell(nt,1)}; end     %Phi{:}(:) = {cell(nt,1)};
                                                % polarization: is a measure of
                                                % the global ordering degree in
                                                % the flock.
                                                % (from https://doi.org/10.1073/pnas.1005766107)

Flu = cell(ne,1); Flu(:) = {cell(nb,1)};
for e=1:ne, Flu{e,1}(:) = {cell(nt,1)}; end


H = cell(ne,1); H(:) = {cell(nb,1)};
for e=1:ne, H{e,1}(:) = {cell(nb,1)}; end

% bird configuration over time
sts = cell(ne,1); sts(:) = {cell(nb,1)};
for e=1:ne, sts{e,1}(:) = {cell(nt,1)}; end

% stress state over time
std = cell(ne,1); sts(:) = {cell(nb,1)};
for e=1:ne, sts{e,1}(:) = {cell(nt,1)}; end


% length policy per step
T = 2;

D   = cell(nn,1);
st  = cell(nn,1);
B   = cell(nn,1);
ns  = zeros(nn,1);
W   = cell(nn,1);
idx = cell(nn,1);
aA  = cell(nn,1);
A = cell(nn,1);
C = cell(nn,1);
o = cell(nn,1);

% For every epoch
%--------------------------------------------------------------------------
for e = 1:ne

    % For every trial
    %----------------------------------------------------------------------
    for b = 1:nb
        
        t_post = zeros(nn,1); 
        % For every time step
        %------------------------------------------------------------------
        for t = 1:nt
            ckd          = zeros(nn,1);
            
            sts{e}{b}{t} = zeros(nn,1);
            std{e}{b}{t} = zeros(nn,1);

            % Asynch updating
            if asynch
                nn2up = randsample(nn,round(nn*0.01*asynchUpdtPercent));
            end


            for i = 1:nn
                if e==1 && b==1 && t==1

                    % B matrix
                    %------------------------------------------------------
                    for u = 1:nu
                        ucell = zeros(nu,1);    ucell(u) = 1;
                        try
                            B{i}{1}(:,:,u) = spm_softmax(repmat(ucell,1,nu),precB(i));
                        catch
                            B{i}{1}(:,:,u) = spm_softmax(repmat(ucell,1,nu),precB);
                        end

                        B{i}{2}(:,:,u)=eye(2); 
                    end

                    % the adjacency matrix
                    %------------------------------------------------------
                    W{i} = buildW(i,nn,nh);
                    ns(i) = sum(W{i});

                    % A matrix (likelihood):
                    %------------------------------------------------------
                    idx{i} = find(W{i});
                    aA{i} = cell(ns(i),1);

                    for s = 1:ns(i)
                        aA{i}{s} = buildA(i,idx{i}(s),nn,nu,vm,ca,fc);
                    end
                end

                s2ck=[i,idx{i}(:)'];              
                for s=1:(ns(i)+1)
                    if ~ckd(s2ck(s),1)
                        [st{s2ck(s)},D{s2ck(s)},t_post(s2ck(s))]=setStateNinitBelief(s2ck(s),MDP,B,predators,T_refract,e,b,t,nt,pu,conf);
                        ckd(s2ck(s),1)=1;
                    end

                    if s>1
                        vecC = zeros(2*nu,1);
                        
                        if st{s2ck(s)}.d<2                          
                            try
                                A{i}{s-1} = softmaxA(aA{i}{s-1},precAbird(i,s2ck(s)),0);
                            catch
                                A{i}{s-1} = softmaxA(aA{i}{s-1},precAbird,0);
                            end

                            % Observations
                            %--------------------------------------------------
                            try
                                try
                                    try
                                        o{i}(s-1,1) = 2*MDP{e}{b}{t-1}{s2ck(s)}.s(1,T)-1;
                                    catch
                                        o{i}(s-1,1) = 2*MDP{e}{b-1}{nt}{s2ck(s)}.s(1,T)-1;
                                    end
                                catch
                                    o{i}(s-1,1) = 2*MDP{e-1}{nb}{nt}{s2ck(s)}.s(1,T)-1;
                                end
                            catch
                                o{i}(s-1,1) = 2*st{s2ck(s)}.s-1;
                            end

                            vecC(o{i}(s-1,1)) = 1;
                        else

                            try
                                A{i}{s-1} = softmaxA(aA{i}{s-1},0,precApred(i,s2ck(s)));
                            catch
                                A{i}{s-1} = softmaxA(aA{i}{s-1},0,precApred);
                            end

                            % Observations
                            %--------------------------------------------------
                            o{i}(s-1,1) = 2*st{s2ck(s)}.s;

                            vecC(o{i}(s-1,1)) = -1;
                        end

                        % Priors
                        %--------------------------------------------------
                        try
                            C{i}{s-1,1} = spm_softmax(vecC,precC(s2ck(s),i));
                        catch
                            C{i}{s-1,1} = spm_softmax(vecC,precC);
                        end
                    else
                        sts{e}{b}{t}(i,1)=st{i}.s;
                        std{e}{b}{t}(i,1)=st{i}.d;
                    end
                end


                % Parameter setting for Active Inference
                %------------------------------------------------------
                mdp.A = A{i};
                mdp.B = B{i};
                mdp.C = C{i};

                
                %stress state dynamics
                %------------------------------------------------------
                out=cellfun(@(x) x.d>1, {st{s2ck(2:end)}});           
                
            
                if st{i}.d==1 
                    if t_post(i) > T_refract
                        if any(out)
                            mdp.s(:,1) = [st{i}.s,2]';
                            mdp.D      = {D{i}{1},[0,1]'};
                            mdp.t_post = 0;
                        else
                            mdp.s(:,1) = [st{i}.s,1]';  
                            mdp.D      = {D{i}{1},[1,0]'};
                            mdp.t_post = t_post(i);
                        end
                    else
                        mdp.s(:,1) = [st{i}.s,1]'; 
                        mdp.D      = {D{i}{1},[1,0]'}; 
                        mdp.t_post=t_post(i)+1;
                    end
                else
                    prob   =  D{i}{2}(2)*exp(-1/tau);
                    D_2    =  [1-prob,prob]';
                    mdp.s(:,1) = [st{i}.s,1+round(prob)]';
                    mdp.D      = {D{i}{1},D_2};
                end
                %

                % Active inference execution
                %------------------------------------------------------
                mdp.o = o{i};

                mdp.T = T;
                mdp.V = repmat(1:nu,T,1); 

                if ~isempty(predators{1,t}) && isKey(predators{1,t},string(i))
                    MDP{e}{b}{t}{i}=mdp;
                    continue
                end

                switch asynch
                    case 0
                        MDP{e}{b}{t}{i} = active_inference_bird_control(mdp);                        
                    case 1
                        if any(nn2up == i)
                            MDP{e}{b}{t}{i} = active_inference_bird_control(mdp);
                        else
                            try
                                MDP{e}{b}{t}{i} = MDP{e}{b}{t-1}{i};
                            catch
                                
                                mdp.u = st{i}.s*ones(1,T);
                                tempX1=zeros(nu,T); tempX1(st{i}.s,:)= ones(1,T);
                                tempX2=zeros(2,T); tempX2(st{i}.d,:)= ones(1,T);
                                mdp.X{1}=spm_softmax(tempX1);
                                mdp.X{2}=spm_softmax(tempX2);

                                MDP{e}{b}{t}{i} = mdp;
                            end
                        end  
                end
            end
            %
            Phi{e}{b}{t} =  measurePhi(MDP{e}{b}{t});
            plotFlock(st,predators{1,t},t);

           % movie frame generation
           % f = getframe;
           % [im,map] = rgb2ind(f.cdata,256,'nodither');
           % im(1,1,1,20) = 0;


            H{e}{b}{t} = compHamiltonian(MDP{e}{b}{t},1);
        end
    end
end

% movie generation
%imwrite(im,map,'Flock.gif','DelayTime',0,'LoopCount',inf) %g443800

vPhi = vertcat(Phi{:});
figure('Name','Phi-value series','NumberTitle','off');
plot(1:ne*nb*nt,cell2mat([vPhi{:}]))

v_avgFE = vertcat(H{:});
figure('Name','Hamiltonian (averaged values)','NumberTitle','off');
plot(1:ne*nb*nt,cell2mat([v_avgFE{:}]))

showFlockBehav(sts,predators);

if yesFigWithPredators
    showFlockBehav(std,predators,'stress');
end


%**************************************************************************
%**** Aux. Fun. ***********************************************************
%**************************************************************************


function [y] = spm_softmax(x,k)

if nargin > 1, x = k*x; end

x  = exp(bsxfun(@minus,x,max(x)));
y  = bsxfun(@rdivide,x,sum(x));



%%%

function MDP = defineMDP(ne,nb,nt,nn)

MDP = cell(ne,1);
for e=1:ne
    MDP{e} = {cell(nb,1)};
    for b=1:nb
        MDP{e}{b} = {cell(nt,1)};
        for t=1:nt
            MDP{e}{b}{t}={cell(nn,1)};
        end
    end
end

%%%

function W = buildW(i,nn,nh)

% figure with label of the 8-size-neighbourhood of i:
%
%       5   1   8
%       3   i   4
%       7   2   6
%

W = zeros(nn,1);
l = sqrt(nn);       


if nh>0
    if mod(i,l)~=1
        W(i-1,1) = 1;
    end
end
if nh>1
    if mod(i,l)~=0
        W(i+1,1) = 1;
    end
end
if nh>2
    if i>l
        W(i-l,1) = 1;
    end
end
if nh>3
   if i<=(nn-l)
       W(i+l,1) = 1;
   end
end
if nh>4
    if mod(i,l)~=1 && i>l
        W(i-l-1,1) = 1;
    end
end
if nh>5
    if mod(i,l)~=0 && i<=(nn-l)
        W(i+l+1,1) = 1;
    end
end
if nh>6
    if mod(i,l)~=0 && i>l
        W(i-l+1,1) = 1;
    end
end
if nh>7
    if mod(i,l)~=1 && i<=(nn-l)
        W(i+l-1,1) = 1;
    end
end

%%%

function Ai = buildA(i,nidx,nn,nu,vm,ca,fc) 

% 8-size-neighbourhood of i:
%
%       5   1   8
%       3   i   4
%       7   2   6
%

l=sqrt(nn);

Ab=zeros(2*nu,nu);
Ap=zeros(2*nu,nu);


uv =[0,1; 0,-1; -1,0; 1,0; ...
    -0.7071,0.7071; 0.7071,-0.7071; -0.7071,-0.7071; 0.7071,0.7071];


for o=1:nu
    for s=1:nu
        A_o_s=uv(o,:)*uv(s,:)';

        if s~=o
            Ab(2*o-1,s) =  fc*A_o_s;
        else
            Ab(2*o-1,s) = vm;
        end
        Ab(2*o,s) = 1/nu;

        if s==o
            Ap(2*o,s) = -vm;
        else
            Ap(2*o,s) = -fc*A_o_s;
        end
        Ap(2*o-1,s) = 1/nu;
        
     end
end

Ai(:,:,1)=compAexceps(Ab,i,nidx,nu,l,ca,1);
Ai(:,:,2)=compAexceps(Ap,i,nidx,nu,l,ca,2);


%%%

function Aa = compAexceps(Aa,i,nidx,nu,l,ca,d)

% if the neighbour nidx is at:
% top
switch d
    case 1
        if (i-nidx) == 1
            Aa(2*2-1,1) = -ca;
            if nu > 4
                Aa(2*6-1,8) = -ca;
                Aa(2*7-1,5) = -ca;
            end
        end
        % down
        if (i-nidx) == -1
            Aa(2*1-1,2)=-ca;
            if nu > 4
                Aa(2*8-1,6) = -ca;
                Aa(2*5-1,7) = -ca;
            end
        end
        % left
        if (i-nidx)== l
            Aa(2*4-1,3)=-ca;
            if nu > 4
                Aa(2*8-1,5) = -ca;
                Aa(2*6-1,7) = -ca;
            end
        end
        % right
        if (i-nidx)== -l
            Aa(2*3-1,4)=-ca;
            if nu>4
                Aa(2*5-1,8)=-ca;
                Aa(2*7-1,6)=-ca;
            end
        end
        % top-left
        if (i-nidx)== l+1
            Aa(2*4-1,1)=-ca;
            Aa(2*2-1,3)=-ca;
            if nu>4
                Aa(2*6-1,5)=-ca;
            end
        end
        % down-right
        if (i-nidx)==-(l+1)
            Aa(2*1-1,4)=-ca;
            Aa(2*3-1,2)=-ca;
            if nu>4
                Aa(2*5-1,6)=-ca;
            end
        end
        % down-left
        if (i-nidx)== l-1
            Aa(2*1-1,3)=-ca;
            Aa(2*4-1,2)=-ca;
            if nu>4
                Aa(2*8-1,7)=-ca;
            end
        end
        % top-right
        if (i-nidx)== -(l-1)
            Aa(2*3-1,1)=-ca;
            Aa(2*2-1,4)=-ca;
            if nu>4
                Aa(2*7-1,8)=-ca;
            end
        end
    otherwise
        if (i-nidx) == 1
            Aa(2*2,1) = -ca;
            if nu > 4
                Aa(2*6,8) = -ca;
                Aa(2*7,5) = -ca;
            end
        end
        % down
        if (i-nidx) == -1
            Aa(2*1,2)=-ca;
            if nu > 4
                Aa(2*8,6) = -ca;
                Aa(2*5,7) = -ca;
            end
        end
        % left
        if (i-nidx)== l
            Aa(2*4,3)=-ca;
            if nu > 4
                Aa(2*8,5) = -ca;
                Aa(2*6,7) = -ca;
            end
        end
        % right
        if (i-nidx)== -l
            Aa(2*3,4)=-ca;
            if nu>4
                Aa(2*5,8)=-ca;
                Aa(2*7,6)=-ca;
            end
        end
        % top-left
        if (i-nidx)== l+1
            Aa(2*4,1)=-ca;
            Aa(2*2,3)=-ca;
            if nu>4
                Aa(2*6,5)=-ca;
            end
        end
        % down-right
        if (i-nidx)==-(l+1)
            Aa(2*1,4)=-ca;
            Aa(2*3,2)=-ca;
            if nu>4
                Aa(2*5,6)=-ca;
            end
        end
        % down-left
        if (i-nidx)== l-1
            Aa(2*1,3)=-ca;
            Aa(2*4,2)=-ca;
            if nu>4
                Aa(2*8,7)=-ca;
            end
        end
        % top-right
        if (i-nidx)== -(l-1)
            Aa(2*3,1)=-ca;
            Aa(2*2,4)=-ca;
            if nu>4
                Aa(2*7,8)=-ca;
            end
        end        
end

%%%

function sftmaxA = softmaxA(A,precAbird,precApred)

sftmaxA(:,:,1)=spm_softmax(A(:,:,1),precAbird);
sftmaxA(:,:,2)=spm_softmax(A(:,:,2),precApred);

%%%

function  [st_i,D_i_1,t_i] = setStateNinitBelief(i,MDP,B,predators,T_r,e,b,t,nt,pu,conf)

if ~isempty(predators{1,t}) && isKey(predators{1,t},string(i))
    if predators{1,t}(string(i))>0  
        st_i.s = predators{1,t}(string(i));
    else 
        st_i.s  = find(rand < cumsum(pu),1); 
    end
    st_i.d = 2; 
    D_i_1{1}=zeros(size(B{i}{1},1),1);    D_i_1{1}(st_i.s)=1;
    D_i_1{2}=[0,1]';
    t_i  = T_r+1;
else
    try
        try
            try
               u = MDP{e}{b}{t-1}{i}.u(:,end-1);
               D_i_1{1} = B{i}{1}(:,:,u) * MDP{e}{b}{t-1}{i}.X{1}(:,1); 
               D_i_1{2} = MDP{e}{b}{t-1}{i}.D{2};
               %
               st_i.s = MDP{e}{b}{t-1}{i}.s(1,end);
               st_i.d = MDP{e}{b}{t-1}{i}.s(2,end);

               t_i = MDP{e}{b}{t-1}{i}.t_post;
               
            catch
               u = MDP{e}{b-1}{nt}{i}.u(:,end-1);
               D_i_1{1} = B{i}{1}(:,:,u) * MDP{e}{b-1}{nt}{i}.X{1}(:,1);
               D_i_1{2} = MDP{e}{b-1}{nt}{i}.D{2};
               %
               st_i.s = MDP{e}{b-1}{nt}{i}.s(1,end);
               st_i.d = MDP{e}{b-1}{nt}{i}.s(2,end);

               t_i    = MDP{e}{b-1}{nt}{i}.t_post;
            end
        catch
           u = MDP{e-1}{nb}{nt}{i}.u(:,end-1);
           D_i_1{1} = B{i}{1}(:,:,u) * MDP{e-1}{nb}{nt}{i}.X{1}(:,1);
           D_i_1{2} = MDP{e-1}{nb}{nt}{i}.D{2};
           %
           st_i.s = MDP{e-1}{nb}{nt}{i}.s(1,end);
           st_i.d = MDP{e-1}{nb}{nt}{i}.s(2,end);

           t_i    = MDP{e-1}{nb}{nt}{i}.t_post;
        end
    catch
        D_i_1{1} = pu;
        D_i_1{2} = [1,0]';
        try
            st_i.s = conf{i}.s;
            st_i.d = conf{i}.d;
        catch
            st_i.s  = find(rand < cumsum(pu),1);
            st_i.d = 1;
        end
        t_i = T_r+1;
    end
end


%%%

% function danger=isInDanger(i,e,b,t,MDP)
% 
% danger=false;
% 
% if t>1
%     try
%         try
%            if MDP{e}{b}{t-1}{i}.s(2,end)==1
%                danger=true;
%            end
%         catch
%            if MDP{e}{b-1}{end}{i}.s(2,end)==1
%                danger=true;
%            end
%         end
%     catch
%        if MDP{e-1}{end}{end}{i}.s(2,end)==1
%             danger=true;
%        end
%     end    
% end

%%%

function Phi = measurePhi(MDP_e_b_t) 

Phi = zeros(2,1); 

nn = numel(MDP_e_b_t(:));
for n=1:nn
    switch MDP_e_b_t{n}.s(1,end)
        case 1
            Phi = Phi + [0;1];
        case 2
            Phi = Phi + [0;-1];
        case 3
            Phi = Phi + [-1;0];
        case 4
            Phi = Phi + [1;0];
        case 5
            Phi = Phi + [-0.7071;0.7071];
        case 6
            Phi = Phi + [0.7071;-0.7071];
        case 7
            Phi = Phi + [-0.7071;-0.7071];
        case 8
            Phi = Phi + [0.7071;0.7071];
    end
end
Phi = norm(Phi/nn);

%%%

function H = compHamiltonian(MDP_e_b_t,h)
H = sum(cellfun(@(x) numel(find(x.o(end,:)== x.s(end))) - h*x.s(end),MDP_e_b_t));

%%%

function plotFlock(st,predator_t,t)

nn = numel(st(:));

L = sqrt(nn);

if t>1
    annotations = findall(gcf(), 'Type', 'annotation');
    delete(annotations);
else
    figure
    xlim([0 L])
    ylim([0 L])
    set(gca,'nextplot','replacechildren','visible','off')
    set(gca,'FontSize',24); 
end

pos = get(gca, 'Position');

ypt = @(i) (i - min(ylim))/diff(ylim) * pos(4) + pos(2);
xpt = @(j) (j - min(xlim))/diff(xlim) * pos(3) + pos(1);

for n=1:nn
    [I,J] = ind2sub([L,L],n);
    
    if ~isempty(predator_t) && isKey(predator_t,string(n))
        acolor='red';
    else
        acolor='black';
    end
    
    switch st{n}.s
      case 1
        annotation('arrow',[xpt(J-.5),xpt(J-.5)],[ypt(L-I+.5),ypt(L-I+1)],'Linewidth',1,'Color',acolor);
      case 2
        annotation('arrow',[xpt(J-.5),xpt(J-.5)],[ypt(L-I+.5),ypt(L-I)],'Linewidth',1,'Color',acolor);
      case 3
        annotation('arrow',[xpt(J-.5),xpt(J-1)],[ypt(L-I+.5),ypt(L-I+.5)],'Linewidth',1,'Color',acolor);
      case 4
        annotation('arrow',[xpt(J-.5),xpt(J)],[ypt(L-I+.5),ypt(L-I+.5)],'Linewidth',1,'Color',acolor);
      case 5
        annotation('arrow',[xpt(J-.5),xpt(J-1)],[ypt(L-I+.5),ypt(L-I+1)],'Linewidth',1,'Color',acolor);
      case 6
        annotation('arrow',[xpt(J-.5),xpt(J)],[ypt(L-I+.5),ypt(L-I)],'Linewidth',1,'Color',acolor);
      case 7
        annotation('arrow',[xpt(J-.5),xpt(J-1)],[ypt(L-I+.5),ypt(L-I)],'Linewidth',1,'Color',acolor);
      case 8
        annotation('arrow',[xpt(J-.5),xpt(J)],[ypt(L-I+.5),ypt(L-I+1)],'Linewidth',1,'Color',acolor);
    end
end
set(gcf, 'Name', strcat('t=',string(t)))
drawnow

%%%%%

function showFlockBehav(st,predators,OPTION)

try
    if strcmp(OPTION,'stress')
        stress =1;
    else
        stress=0;
    end
catch
    stress=0;
end

try
    S = cellfun(@(x)[x{:}],st{:},'UniformOutput',false);
    nn = size(S{:},1);
catch
    S = st;
    nn = size(S,1);
end

L = sqrt(nn);

try
    data(:,:,:) = reshape(S{:},L,L,size(S{:},2));
catch
    data(:,:,:) = reshape(S,L,L,size(S,2));
end

nslice = size(data,3);

slice = 1;
h = struct;
if ~stress
    h.f = figure('Name','Heading direction configuration','NumberTitle','off');
else
    h.f = figure('Name','Stress state configuration','NumberTitle','off');
end
set(h.f,'doublebuffer','on')
h.data = data;

inst_data = squeeze(data(:,:,slice));

xlim([0 L])
ylim([0 L])
xticks(1:L)
yticks(1:L)
xticklabels({})
yticklabels({})
grid on  

try
    showDiffusionPlot(inst_data,predators{1,slice},stress);
catch
    showDiffusionPlot(inst_data,[],stress);  
end

if 1/nslice > .1
    ss1 = .01;
    ss2 = 1/nslice;
else
    ss1=1/nslice;
    ss2=.1;
end

sgtitle({'Time: ',num2str(slice)},'FontSize',24,'FontWeight','Bold')

h.slider1=uicontrol('Parent',h.f,...
'Units','Normalized',...
'Position',[0.1 0.04 0.8 0.05],...
'Style','slider',...
'Min',1,'Max',nslice,...
'SliderStep',[ss1 ss2],...
'Value',1,...
'Callback',{@slider_Callback,data,predators,L,stress});

guidata(h.f,h)


function showDiffusionPlot(data,predators_t,stress) %(st,nn,predators_t)

% 8-size-neighbourhood of i:
%
%       5   1   8
%       3   i   4
%       7   2   6
%

L = size(data,1);

pos = get(gca, 'Position');

ypt = @(i) (i - min(ylim))/diff(ylim) * pos(4) + pos(2);
xpt = @(j) (j - min(xlim))/diff(xlim) * pos(3) + pos(1);

for I=1:L
    for J=1:L
        if ~isempty(predators_t) && isKey(predators_t,string(sub2ind([L L],I,J)))
            acolor='red';
        else
            if ~stress
                acolor='black';
            else
                if data(I,J)==1
                    acolor='cyan';
                else
                    acolor='magenta';
                end                
            end
        end
        
        if ~stress
            switch data(I,J)
                case 1
                    annotation('arrow',[xpt(J-.5),xpt(J-.5)],[ypt(L-I+.5),ypt(L-I+1)],'Linewidth',1,'Color',acolor);
                case 2
                    annotation('arrow',[xpt(J-.5),xpt(J-.5)],[ypt(L-I+.5),ypt(L-I)],'Linewidth',1,'Color',acolor);
                case 3
                    annotation('arrow',[xpt(J-.5),xpt(J-1)],[ypt(L-I+.5),ypt(L-I+.5)],'Linewidth',1,'Color',acolor);
                case 4
                    annotation('arrow',[xpt(J-.5),xpt(J)],[ypt(L-I+.5),ypt(L-I+.5)],'Linewidth',1,'Color',acolor);
                case 5
                    annotation('arrow',[xpt(J-.5),xpt(J-1)],[ypt(L-I+.5),ypt(L-I+1)],'Linewidth',1,'Color',acolor);
                case 6
                    annotation('arrow',[xpt(J-.5),xpt(J)],[ypt(L-I+.5),ypt(L-I)],'Linewidth',1,'Color',acolor);
                case 7
                    annotation('arrow',[xpt(J-.5),xpt(J-1)],[ypt(L-I+.5),ypt(L-I)],'Linewidth',1,'Color',acolor);
                case 8
                    annotation('arrow',[xpt(J-.5),xpt(J)],[ypt(L-I+.5),ypt(L-I+1)],'Linewidth',1,'Color',acolor);
            end
        else
            drawpoint('Position',[J-.5 L-I+.5],'Color',acolor);  
        end
    end
end

%%%%

function slider_Callback(hObject,eventdata,data,predators,L,stress)

h=guidata(hObject);%retrieve struct
slice_i = round(get(h.slider1, 'Value'));

%
inst_data  = squeeze(data(:,:,slice_i)); 

xlim([0 L])
ylim([0 L])
xticks(1:L)
yticks(1:L)
ylim([0 L])
xticklabels({})
yticklabels({})
grid on  

set(gca,'FontSize',24); 
    
delete(findall(gcf,'type','annotation'))

try
    showDiffusionPlot(inst_data,predators{1,slice_i},stress); 
catch
    showDiffusionPlot(inst_data,[],stress); 
end
set(gca,'FontSize',24); 

sgtitle({'Time: ',num2str(slice_i)},'FontSize',24,'FontWeight','Bold')
drawnow

%%%%

%EOF
