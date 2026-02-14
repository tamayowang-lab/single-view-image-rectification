% AFF2SIM - Affine rectification to similarity transformation
%
% This script takes an image and two pairs of orthogonal lines in the world
% (which appear non-orthogonal in the image due to affine distortion)
% and computes a transformation that makes them orthogonal again.
%
% The user selects 2 points on each of 4 lines (2 pairs of orthogonal lines)

% Load image
fim = 'IMG_6741.jpeg'; % Change as needed
im = imread(fim);
[Nr, Nc, N] = size(im);
if N > 1
    im = rgb2gray(im(:,:,1:min(3,N)));
end

figure(1);
subplot(1,2,1);
imshow(im);
hold on;
title('Select 2 points on each of 4 lines (2 orthogonal pairs)');

%%%%%%%%%%%%%%%%%%%%%%
% User input: Select lines
% Blue pair (l1, m1) - first orthogonal pair
% Red pair (l2, m2) - second orthogonal pair
%%%%%%%%%%%%%%%%%%%%%%

disp('Select 2 points on LINE 1 (blue pair)');
[x, y] = ginput(2);
p1_1 = [x(1); y(1); 1];
p1_2 = [x(2); y(2); 1];
l1 = cross(p1_1, p1_2);
l1 = l1 / l1(3);
plot(x, y, 'bo-', 'LineWidth', 2, 'MarkerSize', 8);
hline(l1, 'blue');

disp('Select 2 points on LINE 2 (blue pair) - orthogonal to Line 1');
[x, y] = ginput(2);
p2_1 = [x(1); y(1); 1];
p2_2 = [x(2); y(2); 1];
m1 = cross(p2_1, p2_2);
m1 = m1 / m1(3);
plot(x, y, 'bo-', 'LineWidth', 2, 'MarkerSize', 8);
hline(m1, 'blue');

disp('Select 2 points on LINE 3 (red pair)');
[x, y] = ginput(2);
p3_1 = [x(1); y(1); 1];
p3_2 = [x(2); y(2); 1];
l2 = cross(p3_1, p3_2);
l2 = l2 / l2(3);
plot(x, y, 'ro-', 'LineWidth', 2, 'MarkerSize', 8);
hline(l2, 'red');

disp('Select 2 points on LINE 4 (red pair) - orthogonal to Line 3');
[x, y] = ginput(2);
p4_1 = [x(1); y(1); 1];
p4_2 = [x(2); y(2); 1];
m2 = cross(p4_1, p4_2);
m2 = m2 / m2(3);
plot(x, y, 'ro-', 'LineWidth', 2, 'MarkerSize', 8);
hline(m2, 'red');

hold off;

%%%%%%%%%%%%%%%%%%%%%%
% Compute the Image of the Circular Points
%%%%%%%%%%%%%%%%%%%%%%
% For orthogonal lines l and m: l^T * C_inf * m = 0
% where C_inf is the image of the absolute conic
% C_inf = [s   0  ]
%         [0   s  ]
%         [0   0  0]
% 
% From two orthogonal line pairs, we get two constraints:
% l1^T * C_inf * m1 = 0
% l2^T * C_inf * m2 = 0
%
% This gives us: l1(1)*m1(1)*s + l1(2)*m1(2)*s = 0
%                l2(1)*m2(1)*s + l2(2)*m2(2)*s = 0
%
% We can solve for s, but for simplicity, we use the dual conic approach

% Set up the constraint equations
% l^T * C_inf * m = 0 becomes:
% [l(1) l(2) l(3)] * [s 0 0; 0 s 0; 0 0 0] * [m(1); m(2); m(3)] = 0
% = l(1)*s*m(1) + l(2)*s*m(2) = 0
% = s * (l(1)*m(1) + l(2)*m(2)) = 0

% For two orthogonal line pairs, we have:
% l1(1)*m1(1) + l1(2)*m1(2) = 0  (should be satisfied after rectification)
% l2(1)*m2(1) + l2(2)*m2(2) = 0  (should be satisfied after rectification)

% Build constraint matrix for dual conic S = [s11 s12; s12 s22]
% Each orthogonality constraint gives: [l(1)*m(1), l(1)*m(2)+l(2)*m(1), l(2)*m(2)] * [s11; s12; s22] = 0

A = [l1(1)*m1(1), l1(1)*m1(2) + l1(2)*m1(1), l1(2)*m1(2);
     l2(1)*m2(1), l2(1)*m2(2) + l2(2)*m2(1), l2(2)*m2(2)];

% For affine images, we typically assume s12 = 0 (no skew)
% So we solve: [l(1)*m(1), l(2)*m(2)] * [s11; s22] = 0

% Simplified approach: assume square pixels (s11 = s22)
% Then: (l1(1)*m1(1) + l1(2)*m1(2)) = 0
%       (l2(1)*m2(1) + l2(2)*m2(2)) = 0

% Alternative: use SVD to find the null space
[U, S, V] = svd(A);
s_vec = V(:, end); % Last column of V (smallest singular value)

% Reconstruct S matrix
S = [s_vec(1), s_vec(2);
     s_vec(2), s_vec(3)];

% Ensure S is positive definite
if det(S) < 0
    S = -S;
end

% Compute the rectifying transformation from S
% S = A * A^T, so A = chol(S)' (Cholesky decomposition)
try
    A_mat = chol(S, 'lower');
catch
    warning('S is not positive definite. Using absolute value of eigenvalues.');
    [V_eig, D_eig] = eig(S);
    D_eig = abs(D_eig);
    A_mat = V_eig * sqrt(D_eig);
end

% The affine rectification matrix
H_aff = [A_mat, [0; 0];
         0, 0, 1];

%%%%%%%%%%%%%%%%%%%%%%
% Apply transformation
%%%%%%%%%%%%%%%%%%%%%%
[om, nT] = imTrans(im, H_aff);

subplot(1,2,2);
imshow(om);
title('Affine Rectified Image');
hold on;

% Transform the lines
l1_new = inv(H_aff)' * l1;
m1_new = inv(H_aff)' * m1;
l2_new = inv(H_aff)' * l2;
m2_new = inv(H_aff)' * m2;

% Apply newT transformation
l1_rect = inv(nT)' * l1_new;
m1_rect = inv(nT)' * m1_new;
l2_rect = inv(nT)' * l2_new;
m2_rect = inv(nT)' * m2_new;

hline(l1_rect, 'blue');
hline(m1_rect, 'blue');
hline(l2_rect, 'red');
hline(m2_rect, 'red');

% Verify orthogonality
angle1 = acosd(abs(l1_rect(1)*m1_rect(1) + l1_rect(2)*m1_rect(2)) / ...
               (norm(l1_rect(1:2)) * norm(m1_rect(1:2))));
angle2 = acosd(abs(l2_rect(1)*m2_rect(1) + l2_rect(2)*m2_rect(2)) / ...
               (norm(l2_rect(1:2)) * norm(m2_rect(1:2))));

fprintf('Angle between blue pair: %.2f degrees (should be ~90)\n', angle1);
fprintf('Angle between red pair: %.2f degrees (should be ~90)\n', angle2);

hold off;
