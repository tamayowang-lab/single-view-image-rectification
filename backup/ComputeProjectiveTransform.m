% ComputeProjectiveTransform - Reconstruct world plane from image
%
% This script computes the projective transformation H between image points
% and world plane points using 4 or more point correspondences.
% Given: p = H*P (image point = H * world point)
% Find: H, then compute P = inv(H)*p
%
% The user selects points in the image and provides their world coordinates

% Load image
fim = 'IMG_6741.jpeg'; % Change as needed
im = imread(fim);
[Nr, Nc, N] = size(im);
if N > 1
    im = rgb2gray(im(:,:,1:min(3,N)));
end

figure(1);
imshow(im);
hold on;
title('Select at least 4 points with known world coordinates');

%%%%%%%%%%%%%%%%%%%%%%
% User input: Select image points
%%%%%%%%%%%%%%%%%%%%%%
n_points = 4; % Number of correspondences (minimum 4, can be more)
image_points = zeros(3, n_points);
world_points = zeros(3, n_points);

% Example: For a building facade, you might know:
% - Width and height in meters
% - Distances between features
% You'll need to input real world coordinates

fprintf('\nSelect %d points in the image\n', n_points);
fprintf('After clicking, you will enter world coordinates for each point\n\n');

for i = 1:n_points
    fprintf('Click point %d in image...\n', i);
    [x, y] = ginput(1);
    image_points(:, i) = [x; y; 1];
    plot(x, y, 'ro', 'MarkerSize', 10, 'LineWidth', 2);
    text(x+10, y-10, sprintf('p%d', i), 'Color', 'red', 'FontSize', 14);
end

hold off;

% Input world coordinates
fprintf('\n--- Enter World Coordinates ---\n');
fprintf('Enter coordinates in a consistent unit (e.g., meters, feet)\n');
fprintf('Example: For a rectangular building facade:\n');
fprintf('  Bottom-left: (0, 0, 0)\n');
fprintf('  Bottom-right: (10, 0, 0) if width is 10m\n');
fprintf('  Top-left: (0, 8, 0) if height is 8m\n');
fprintf('  Top-right: (10, 8, 0)\n\n');

for i = 1:n_points
    fprintf('World coordinates for point %d:\n', i);
    X = input(sprintf('  X%d = ', i));
    Y = input(sprintf('  Y%d = ', i));
    Z = input(sprintf('  Z%d (typically 0 for planar) = ', i));
    world_points(:, i) = [X; Y; Z];
end

%%%%%%%%%%%%%%%%%%%%%%
% Compute Homography H using DLT (Direct Linear Transform)
%%%%%%%%%%%%%%%%%%%%%%
% For each correspondence: p_i = H * P_i
% In inhomogeneous form: [u_i; v_i; 1] = H * [X_i; Y_i; 1]
% (assuming Z=0 for planar world, we can drop the third coordinate)
%
% This gives us:
% u_i = (h11*X_i + h12*Y_i + h13) / (h31*X_i + h32*Y_i + h33)
% v_i = (h21*X_i + h22*Y_i + h23) / (h31*X_i + h32*Y_i + h33)
%
% Rearranging: 
% -h11*X_i - h12*Y_i - h13 + h31*u_i*X_i + h32*u_i*Y_i + h33*u_i = 0
% -h21*X_i - h22*Y_i - h23 + h31*v_i*X_i + h32*v_i*Y_i + h33*v_i = 0

A = zeros(2*n_points, 9);

for i = 1:n_points
    X = world_points(1, i);
    Y = world_points(2, i);
    u = image_points(1, i);
    v = image_points(2, i);
    
    % First equation (for u)
    A(2*i-1, :) = [-X, -Y, -1, 0, 0, 0, u*X, u*Y, u];
    
    % Second equation (for v)
    A(2*i, :) = [0, 0, 0, -X, -Y, -1, v*X, v*Y, v];
end

% Solve using SVD
[U, S, V] = svd(A);
h = V(:, end); % Last column of V (smallest singular value)

% Reshape into 3x3 matrix
H = reshape(h, 3, 3)';

% Normalize so H(3,3) = 1
H = H / H(3,3);

fprintf('\n--- Computed Homography Matrix H ---\n');
disp(H);

%%%%%%%%%%%%%%%%%%%%%%
% Verify the transformation
%%%%%%%%%%%%%%%%%%%%%%
fprintf('\n--- Verification ---\n');
fprintf('Checking image = H * world for all points:\n\n');

for i = 1:n_points
    P_world = world_points(:, i);
    p_image_measured = image_points(:, i);
    
    % Project world point to image
    p_image_computed = H * P_world;
    p_image_computed = p_image_computed / p_image_computed(3); % Normalize
    
    % Compute error
    error = norm(p_image_measured(1:2) - p_image_computed(1:2));
    
    fprintf('Point %d:\n', i);
    fprintf('  Measured image: (%.2f, %.2f)\n', p_image_measured(1), p_image_measured(2));
    fprintf('  Computed image: (%.2f, %.2f)\n', p_image_computed(1), p_image_computed(2));
    fprintf('  Error: %.2f pixels\n\n', error);
end

%%%%%%%%%%%%%%%%%%%%%%
% Reconstruct world points from image points
%%%%%%%%%%%%%%%%%%%%%%
fprintf('--- World Reconstruction ---\n');
fprintf('You can now click points in the image to find their world coordinates\n');

figure(2);
imshow(im);
title('Click points to reconstruct world coordinates (right-click to finish)');
hold on;

% Plot the original correspondence points
for i = 1:n_points
    plot(image_points(1,i), image_points(2,i), 'go', 'MarkerSize', 8, 'LineWidth', 2);
end

H_inv = inv(H);

reconstructed_points = [];
button = 1;

while button == 1
    [x, y, button] = ginput(1);
    
    if button == 1
        plot(x, y, 'r+', 'MarkerSize', 12, 'LineWidth', 2);
        
        % Image point (homogeneous)
        p_img = [x; y; 1];
        
        % Reconstruct world point
        P_world = H_inv * p_img;
        P_world = P_world / P_world(3); % Normalize
        
        fprintf('Image point (%.1f, %.1f) -> World point (%.2f, %.2f, %.2f)\n', ...
                x, y, P_world(1), P_world(2), P_world(3));
        
        reconstructed_points = [reconstructed_points, P_world];
    end
end

hold off;

%%%%%%%%%%%%%%%%%%%%%%
% Visualize world coordinates
%%%%%%%%%%%%%%%%%%%%%%
if ~isempty(reconstructed_points)
    figure(3);
    hold on;
    grid on;
    axis equal;
    
    % Plot correspondence points
    plot3(world_points(1,:), world_points(2,:), world_points(3,:), ...
          'go', 'MarkerSize', 12, 'LineWidth', 2);
    
    % Plot reconstructed points
    plot3(reconstructed_points(1,:), reconstructed_points(2,:), reconstructed_points(3,:), ...
          'r+', 'MarkerSize', 12, 'LineWidth', 2);
    
    % Draw the reference plane (Z=0)
    x_range = [min(world_points(1,:))-1, max(world_points(1,:))+1];
    y_range = [min(world_points(2,:))-1, max(world_points(2,:))+1];
    [X_mesh, Y_mesh] = meshgrid(linspace(x_range(1), x_range(2), 10), ...
                                 linspace(y_range(1), y_range(2), 10));
    Z_mesh = zeros(size(X_mesh));
    surf(X_mesh, Y_mesh, Z_mesh, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
    
    xlabel('X (world)');
    ylabel('Y (world)');
    zlabel('Z (world)');
    title('World Coordinate Reconstruction');
    legend('Correspondence points', 'Reconstructed points', 'Reference plane');
    view(45, 30);
    hold off;
end

%%%%%%%%%%%%%%%%%%%%%%
% Save results
%%%%%%%%%%%%%%%%%%%%%%
save('homography_results.mat', 'H', 'H_inv', 'image_points', 'world_points', 'reconstructed_points');
fprintf('\nResults saved to homography_results.mat\n');
