%__author__ = Zed YANG
%% Main Function
function [X,y,X_train,y_train,X_test,y_test,...
          n_features,n_classes,n_obs,Theta1,Theta2,p] = BPNN()
% lamda [1]: Regularization punishment parameter.
% max_iter[1]: Maximum iteration in optimization algo.
% hidden_layer_size [1]: The number of nodes on each hidden layer,
%                        excluded iota.

    lambda = 0.8;
    max_iters = 50;
    train_proportion = 0.75;
    
    [X,y,X_train, y_train, X_test, y_test, ...
     n_features,n_classes,n_obs] = import_partition_data(1,...
                                   'data.mat',train_proportion); 
    hidden_layer_size = min(n_features,25);
    
    [Theta1,Theta2] = train_BPNN2(n_features,...
                                  hidden_layer_size, ...
                                  n_classes, ...
                                  X_train,y_train,lambda,max_iters);
                              
    p = predict_BPNN2(Theta1, Theta2, X);
    p_test = predict_BPNN2(Theta1, Theta2, X_test);
    acc_overall = mean(double(p == y)) * 100;
    acc_testSet = mean(double(p_test == y_test)) * 100;
    fprintf('\nOverall Accuracy: %f\n', acc_overall);
    
    fprintf('\nTest Set Accuracy: %f\n', acc_testSet);
    export(y,p,'pred_data');
end

%% Import and Partition data.
function [X, y, X_train, y_train, X_test, y_test, ...
          n_features, n_classes, n_obs] = ...
            import_partition_data(col_label, file_name, train_proportion)
% [X,y] = import_partition_data(data)
% Partition data into features and label.
%
% data [n m+1]: Data input.
% col_label [1]: Column index of label, 1<=col_labels<=m.
%                if -1, regrad file_name as a structured data.
% file_name [str]: Name of the data file.
% train_proportion [1]: proportion of training set.
% X [n m]: Features matrix.
% y [n 1]: Label vector.
% X_train [n*train_proportion, m]; X_test..
% y_train [n*train_proportion, 1]; y_test..
% n_features [1]: Number of features.
% n_classes [1]: Number of label classes.
% n_obs [1]: Number of observations

    if col_label == -1
        data = load(file_name);
        y = data.y;
        X = data.X;
    else
        data = load(file_name);
        y = data.data(:,col_label);
        X = data.data;
        X(:,col_label) = [];   
    end
    n_features = size(X,2);
    n_obs = size(X,1);
    n_classes=size(unique(y),1);

    % rand index
    [sorted,index] = sort(rand(1,n_obs));
    n_train = ceil(n_obs * train_proportion);

    X_train = X(index(1:n_train),:);
    y_train = y(index(1:n_train),:);
    X_test = X(index(n_train+1:end),:);
    y_test = y(index(n_train+1:end),:);
end

%% Sigmoid Function
function S = sigmoid(X)
% S = sigmoid(X)
% Computes sigmoid of matrix X, elementwise.
%
% X [n m]: An arbitrary real-values matrix.
% S [n m]: A real-valued matrix, by applying \frac{1}{1+\exp(x)}
%           to X elementwise.
    S = 1.0 ./ (1.0 + exp(-X));
end

%% Derivative of Sigmoid Function
function DS = grad_sigmoid(X)
% DS = grad_sigmoid(X)
% Computes derivative(gradient) of sigmoid of matrix X, elementwise.
%
% X [n m]: An arbitrary real-values matrix.
% DS [n m]: A real-valued matrix, by applying 
%           \frac{1}{1+\exp(x)} * \frac{-\exp(x)}{1+\exp(x)}
%           to X elementwise.
    S = sigmoid(X);
    DS = S .* (1 - S);
end

%% Random Initialization
function Theta = rand_init_weights(size_from, size_to)
% Randomized initialization of weights.
% size_from [1]: Size of last layer.
% size_to [1]: Size of next layer.
% Theta [1+size_from size_to]: The weight.

    epsilon = .12; % Size of random disturbance band.
    Theta = rand(1+size_from, size_to) * 2 * epsilon - epsilon;
end

%% Debug tests.
function rolled_Theta = test_weights()
    weights = load('test_weights.mat');
    Theta1 = (weights.Theta1)';
    Theta2 = (weights.Theta2)';
    rolled_Theta = [Theta1(:) ; Theta2(:)];
end

%% 2 Layers Cost Function
function [J,grad_J] = ...
          BPNNCost_2(rolled_Theta, input_layer_size, hidden_layer_size, ...
                     num_classes, X, y, lambda)
% Compute Back-propagation neural network cost function and gradient.
% rolled_Theta [1, #]:
% input_layer_size [1]: The number of features, excluded iota.
% hidden_layer_size [1]: The number of nodes on each hidden layer,
%                        excluded iota.
% num_classes [1]: The number of label classes.
% X [n_obs input_layer_size]: Training input features at first layer.
% y [n_obs 1]: Training set label.
% lamda [1]: Regularization punishment parameter.

    % Make alias.
    n = size(X, 1);         % Number of observations.
    m = input_layer_size;   % Number of features.
    h = hidden_layer_size;  % Number of derived intermediate features.
    k = num_classes;        % Number of label classes.
    
    % X[n,m]; y[n,1]; Theta1[m+1,h]; Theta2[h+1,k]; Y[n,k];
    % breve_Theta1[m,h]; breve_Theta2[h,k]; Delta1[m+1,h]; Delta2[h+1,k]
    % Reshape Theta1 and Theta2.
    Theta1 = reshape(rolled_Theta(1:h*(m+1)), m+1, h);
    Theta2 = reshape(rolled_Theta((1+(h*(m+1))):end), h+1, k);
    
    % Make class indicators
    I = eye(k);
    Y = I(y,:);
    
    % ------------------------------------------------------------
    % Compute J, pure FP.
    iota = ones(n,1);
    tilde_X = [iota, X];
    Z2 = tilde_X * Theta1;      %[n,h] = [n,m+1]*[m+1,h]
    h_Z2 = sigmoid(Z2);         %[n,h]
    tilde_h_Z2 = [iota, h_Z2];  %[n,h+1]
    Z3 = tilde_h_Z2 * Theta2;   %[n,k] = [n,h+1]*[h+1,k]
    h_Z3 = sigmoid(Z3);         %[n,k]
    
    % Compute cost: J_matrix[n,k]; J[1]
    J_matrix = (-Y .* log(h_Z3)) - ((1 - Y) .* log(1 - h_Z3));
    J = (1/n) * sum(J_matrix(:));
    
    % Regularize.
    breve_Theta1 = Theta1(2:end,:);
    breve_Theta2 = Theta2(2:end,:);
    reg_modif = (lambda / (2*n)) * (sumsqr(breve_Theta1(:)) + ...
                sumsqr(breve_Theta2(:)));
    J = J + reg_modif;
    
    % ------------------------------------------------------------
    % Compute grad_J, FP -> BP
    Delta1 = zeros(m+1,h); % cumulated errors.
    Delta2 = zeros(h+1,k);
    
    for i = 1:n % Element wise.
        % FP.
        tilde_x = [1, X(i,:)];          %[1,m+1]
        z2 = tilde_x * Theta1;          %[1,h]=[1,m+1]*[m+1,h]
        tilde_h_z2 = [1, sigmoid(z2)];  %[1,h+1]
        z3 = tilde_h_z2 * Theta2;             %[1,k]=[1,h+1]*[h+1,k]
        h_z3 = sigmoid(z3);             %[1,k]
        % BP.
        yi = Y(i,:);                    %[1,k]
        delta3 = h_z3 - yi;             %[1,k], Last error term.
        delta2 = (delta3 * breve_Theta2') .* grad_sigmoid(z2);
        %[1,k]*[k,h]=[1,h]; [1,h].*[1,h]=[1,h]

        Delta2 = Delta2 + (tilde_h_z2' * delta3);   %[h+1,k]=[h+1,1]*[1,k]
        Delta1 = Delta1 + (tilde_x' * delta2);      %[m+1,h]=[m+1,1]*[1,h]
    end
    % Regularize.
    grad_J_Theta1 = (1/n) * Delta1;     %[h+1,k]
    grad_J_Theta2 = (1/n) * Delta2;     %[m+1,h]
    grad_J_Theta1(2:end,:) = grad_J_Theta1(2:end,:) + ...   %[h,k]
                           ((lambda / n) * breve_Theta1);
    grad_J_Theta2(2:end,:) = grad_J_Theta2(2:end,:) + ...   %[m,h]
                           ((lambda / n) * breve_Theta2);
                       
    grad_J = [grad_J_Theta1(:) ; grad_J_Theta2(:)];
end

%% Check BP grad against numerical diff.
function check_BPNN_grad(lambda)
% TODO
end

%% Train 2 layer model.
function [Theta1,Theta2] = train_BPNN2(input_layer_size, hidden_layer_size, ...
                                       num_classes, X, y, lambda, max_iter)
% Train a model.
% input_layer_size [1]: The number of features, excluded iota.
% hidden_layer_size [1]: The number of nodes on each hidden layer,
%                        excluded iota.
% num_classes [1]: The number of label classes.
% X [n_obs input_layer_size]: Training input features at first layer.
% y [n_obs 1]: Training set label.
% lamda [1]: Regularization punishment parameter.
% max_iter[1]: Maximum iteration in optimization algo.

    init_Theta1 = rand_init_weights(input_layer_size, hidden_layer_size);
    init_Theta2 = rand_init_weights(hidden_layer_size, num_classes);
    % Roll parameters
    init_ThetaVec = [init_Theta1(:) ; init_Theta2(:)];
    options = optimset('MaxIter', max_iter);
    % Run optimization on @param
    cost_func = @(param) BPNNCost_2(param, ...
                                    input_layer_size, ...
                                    hidden_layer_size, ...
                                    num_classes, X, y, lambda);

    [ThetaVec, cost_val] = fmincg(cost_func, init_ThetaVec, options);
    
    % Make alias.
    m = input_layer_size;   % Number of features.
    h = hidden_layer_size;  % Number of derived intermediate features.
    k = num_classes;        % Number of label classes.
    
    % X[n,m]; y[n,1]; Theta1[m+1,h]; Theta2[h+1,k]; Y[n,k];
    % breve_Theta1[m,h]; breve_Theta2[h,k]; Delta1[m+1,h]; Delta2[h+1,k]
    % Reshape Theta1 and Theta2.
    Theta1 = reshape(ThetaVec(1:h*(m+1)), m+1, h);
    Theta2 = reshape(ThetaVec((1+(h*(m+1))):end), h+1, k);
end

%% Predict
function p = predict_BPNN2(Theta1, Theta2, X)
% Predict a BPNN(2) model.
% Theta1 [m+1,h]: Estimated param: First layer -> second layer.
% Theta2 [h+1,k]: Estimated param: Second layer -> final.
%                 in which m=number of features, h=hidden layer size
%                 k=number of unique label classes.
% X [n,m]: Fed features.
    n = size(X,1);
    p = zeros(n,1);
    iota = ones(n,1);
    h1_X = sigmoid([iota, X] * Theta1);     %[n,h]=[n,m+1]*[m+1,h]
    h2_Z2 = sigmoid([iota, h1_X] * Theta2); %[n,k]=[n,h+1]*[h+1,k]
    [dummy, p] = max(h2_Z2, [], 2);
end

%% Export.
function export(y,p,file_name)
% X [n,m]
% p [n,1]: prediction.
% y [n,1]: true label.
    E = [y,p];
    save(file_name,'E');
end




