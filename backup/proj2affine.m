%function proj2affine
fim= 'IMG_6742.jpeg';
im=imread(fim); 
[Nr,Nc,N]= size(im);
if N>1 
    im=rgb2gray(im(:,:,1:min(3,N)));
end
subplot(1,2,1)
imshow(1.6*im); hold on;
f=1;

%%%%%%%%%%%%%%%%%%%%%%
% User click input 
% Or load saved clicks
%%%%%%%%%%%%%%%%%%%%%%
click= 1;
select= 0;
if click,
    if select
        p=[]; l=[];
        colr=['r','b'];
        for i=1:4
            [x y b]=ginput(1); if b~=1, return; end
            plot(x,y,'+','color',colr(1+mod(i,2)));
            x=x/f; y=y/f;
            p=[p [x y 1]'];
        end
        if fim=='IMG_6742.jpeg'
            save POints1New.mat;
        else
            save POints2New.mat;
        end
    else
        if fim=='IMG_6742.jpeg'
            load POints1.mat;
        else
            load POints2.mat;
        end
    end
    for k=1:4
        plot(p(1,k),p(2,k),'ro','markersize',15);
        text(p(1,k),p(2,k)-20,num2str(k),'color','r','fontsize',25)
    end
    p1= p(:,1);
    p2= p(:,2);
    p3= p(:,3);
    p4= p(:,4);
    l21= cross(p2,p1);
    l21= l21'/l21(3);
%    l11=l11/norm(l11);
    l43= cross(p4,p3);
    l43= l43'/l43(3);
%    l12=l12/norm(l12);
    l32= cross(p3,p2);
    l32= l32'/l32(3);
%    l21=l21/norm(l21);
    l41= cross(p4,p1);
    l41= l41'/l41(3);
    hline(l21,'r');
    hline(l43,'r');
    hline(l32,'r');
    hline(l41,'r');
    %pause

    van1= cross(l21,l43);
    van2= cross(l32,l41);
else
    [xo,yo]= ginput(2);
    van1=[xo(1)/f yo(1)/f 1];
    van2=[xo(2)/f yo(2)/f 1];
end
l= cross(van1,van2);
l= l/l(3);
%%%%%%%%%%%%%%%%%%%%%
% Homography
%%%%%%%%%%%%%%%%%%%%%%
H=[1 0 0;
    0 1 0;
    l(:)'];
%%%%%%%%%%%%%%%%%%%%%%
% Result
%%%%%%%%%%%%%%%%%%%%%%
[om nT]=imTrans(im,H); 
subplot(1,2,2)
imshow(om);     
pp=inv(nT)*H*p;
hold on; plot(pp(1,1:4)./pp(3,1:4),pp(2,1:4)./pp(3,1:4),'r+'); 
ll21=inv(inv(nT)*H)'*l21'; hline(ll21,'r'); 
ll43=inv(inv(nT)*H)'*l43'; hline(ll43,'r'); 
ll32=inv(inv(nT)*H)'*l32'; hline(ll32,'r');
ll41=inv(inv(nT)*H)'*l41'; hline(ll41,'r');
hold off;