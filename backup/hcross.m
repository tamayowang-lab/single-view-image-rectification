% HCROSS - Homogeneous cross product, result normalised to s = 1.
%
% Function to form cross product between two points, or lines,
% in homogeneous coodinates.  The result is normalised to lie
% in the scale = 1 plane.
% 
% Usage: c = hcross(a,b)
%

%  Peter Kovesi
%  School of Computer Science & Software Engineering
%  The University of Western Australia
%  pk @ csse uwa edu au
%  http://www.csse.uwa.edu.au/~pk
%
%  April 2000

function c = hcross(a,b)
% Formula of cross product in homogeneous coordinates 
c = cross(a,b);
c = c/c(3);
