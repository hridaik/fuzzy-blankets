% script_execution
%--------------------------------------------------------------------------

% Author: Domenico Maisto


nn = 100;   %number of birds/number of grid cells
nt = 60;    %number of time steps

prompt = "Digit:\n 0: for a simulation without predators\n" + ...
                "1: for a simulation with predators\n>> ";
x = input(prompt);

switch x
    case 0
        [sts,std] = flocking_AIF_simulation;     
    case 1
        create_containers = @(n)arrayfun(@(x)containers.Map(), 1:nt, 'UniformOutput', false);

        tattacks = [5,35];             % attack times 
        dirPred = randi(4,1,2);        % heading direction of the predators
        locPred = randi(nn,1,2);       % predator position at attack times

        param.predators = create_containers(nn);
        param.predators{1,tattacks(1)}(num2str(locPred(1,1))) = dirPred(1,1);
        param.predators{1,tattacks(2)}(num2str(locPred(1,2))) = dirPred(1,2);

        [sts,std] = flocking_AIF_simulation(param);
    otherwise
         error('Error: input must be 0 or 1');         
end



   


