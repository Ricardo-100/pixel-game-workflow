// Deterministic, dependency-free pixel rasterizer. Pixelorama commits and exports the images.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const palette=['#00000000','#334F45','#426248','#537C4D','#649052','#79A65F','#91B970','#B9CF85','#F2DCAC','#D4B07C','#AC855C','#8C6248','#704D3D','#573F3A','#C99860','#E0AE6F','#F3C785','#FFE3A4','#D08262','#AF6556','#448C86','#33726F','#24605F','#6BAB9B','#DCE7C4','#FFF6D4','#F2A096','#DF7080','#8366A1','#AD91B7','#5C989D','#81BAB5','#B9DAD0','#A5B9A0','#E6BA71','#3A3C37'];
function surface(w,h){
 const p=Array.from({length:h},()=>Array(w).fill(0));
 const rect=(x,y,rw,rh,c)=>{for(let j=Math.max(0,y);j<Math.min(h,y+rh);j++)for(let i=Math.max(0,x);i<Math.min(w,x+rw);i++)p[j][i]=c};
 const ellipse=(cx,cy,rx,ry,c)=>{for(let y=Math.max(0,Math.floor(cy-ry));y<=Math.min(h-1,Math.ceil(cy+ry));y++)for(let x=Math.max(0,Math.floor(cx-rx));x<=Math.min(w-1,Math.ceil(cx+rx));x++)if(((x-cx)/rx)**2+((y-cy)/ry)**2<=1)p[y][x]=c};
 const line=(x,y,xx,yy,c)=>{let dx=Math.abs(xx-x),dy=-Math.abs(yy-y),sx=x<xx?1:-1,sy=y<yy?1:-1,e=dx+dy;while(true){rect(x,y,1,1,c);if(x===xx&&y===yy)break;let e2=e*2;if(e2>=dy){e+=dy;x+=sx}if(e2<=dx){e+=dx;y+=sy}}};
 const poly=(pts,c)=>{for(let y=Math.max(0,Math.min(...pts.map(q=>q[1])));y<=Math.min(h-1,Math.max(...pts.map(q=>q[1])));y++)for(let x=0;x<w;x++){let on=false;for(let i=0,j=pts.length-1;i<pts.length;j=i++){const[a,b]=pts[i],[d,e]=pts[j];if((b>y)!=(e>y)&&x<(d-a)*(y-b)/(e-b)+a)on=!on}if(on)p[y][x]=c}};
 return {p,rect,ellipse,line,poly,w,h};
}
function save(s,name){fs.writeFileSync(path.join(root,'source',name+'.json'),JSON.stringify({width:s.w,height:s.h,palette,rows:s.p.map(r=>r.map(c=>String.fromCharCode(65+c)).join(''))}));}
const s=surface(256,128);const {rect:r,ellipse:e,line:l,poly:g}=s;
// Seamless 16px tiles: four grasses, dirt, dry/wet beds, path and pond.
for(let t=0;t<4;t++){
 let x=t*16;r(x,0,16,16,4);
 for(let i=0;i<10;i++){let a=(i*7+t*3)%16,b=(i*11+t*5)%16;r(x+a,b,1,1,i%3===0?6:5);if(a<15&&b>1&&i%3===0){r(x+a+1,b-1,1,1,5);}}
}
r(64,0,16,16,10);for(let i=0;i<12;i++)r(64+(i*7)%16,(i*11)%16,2,1,i%2?9:11);
for(let t=5;t<=6;t++){let x=t*16;r(x,0,16,16,t===5?11:12);r(x+1,1,14,14,t===5?14:11);for(let yy=3;yy<15;yy+=4){r(x+2,yy,12,1,t===5?10:12);r(x+2,yy+1,12,1,t===5?15:10);}r(x+1,1,14,1,t===5?15:10);}
r(112,0,16,16,9);r(113,1,14,14,8);r(114,2,5,4,9);r(121,9,5,5,9);l(115,8,124,8,9);l(120,3,120,6,9);
for(let t=8;t<10;t++){let x=t*16;r(x,0,16,16,30);r(x,2,16,2,31);r(x+2+t%2,9,8,1,32);r(x+8,12,6,1,31);r(x,15,16,1,31);}
// Flower tufts and fence parts, transparent tile row.
for(let t=0;t<3;t++){let x=t*16;l(x+8,30,x+8,24,2);l(x+8,28,x+5,26,5);e(x+8,22,3,2,t===0?25:t===1?27:29);r(x+7,21,2,2,34);}
r(48,20,16,3,11);r(48,21,16,1,15);r(48,26,16,3,11);r(48,26,16,1,15);r(53,17,4,15,12);r(54,18,2,12,15);r(54,17,2,1,17);
// Seed bag, watering can, harvest icon.
r(66,21,12,10,13);r(67,20,10,10,8);r(69,18,6,3,14);e(72,26,3,3,3);r(71,23,2,6,6);
r(82,23,9,7,22);r(82,22,9,6,20);r(84,21,5,2,23);l(90,24,95,20,21);r(94,19,2,3,23);r(80,23,2,5,21);
// Four crop stages use 16x32 cells, baseline y=63.
for(let st=0;st<4;st++){
 let x=st*16;e(x+8,61,6,2,12);
 if(st===0){r(x+6,58,2,1,8);r(x+10,60,2,1,9);continue;}
 l(x+8,60,x+8,st===1?54:48,2);
 e(x+5,st===1?55:51,3,2,5);e(x+11,st===1?53:48,3,2,6);
 if(st>=2){e(x+5,46,4,3,3);e(x+10,44,4,3,5);l(x+7,53,x+9,44,6);}
 if(st===3){e(x+8,57,5,5,13);e(x+8,56,4,4,24);e(x+7,55,3,3,25);r(x+7,60,2,3,24);e(x+6,48,4,2,5);e(x+11,47,4,2,6);}
}
// Apple tree, 32x48 at 80,32.
e(96,76,13,3,2);r(93,55,7,21,12);r(94,55,4,20,14);r(94,71,2,5,10);l(97,62,103,56,11);
e(96,49,15,14,1);e(87,51,8,10,1);e(104,50,8,10,1);e(96,45,13,12,3);e(86,48,7,8,3);e(104,47,8,9,4);e(92,41,9,7,5);e(101,44,7,5,5);e(87,44,4,4,6);
for(const[a,b]of[[87,51],[99,40],[104,52],[94,56]]){e(a,b,2,2,19);r(a-1,b-1,2,2,27);r(a,b-3,1,1,7);}
// Cottage 64x64 cell at 128,48, roof at 55..81, floor at 105.
e(160,108,29,4,2);r(135,77,50,30,12);r(137,78,46,27,8);r(137,99,46,6,9);r(140,80,40,2,17);
g([[131,78],[144,57],[176,57],[190,78]],13);g([[134,76],[146,59],[174,59],[186,76]],19);
for(let y=61;y<77;y+=4){l(145-(y-61)/2,y,176+(y-61)/2,y,18);}
r(168,52,7,14,12);r(169,52,5,12,10);r(168,51,8,3,8);
r(153,85,14,22,12);r(155,86,10,21,20);r(155,86,10,3,21);r(163,97,1,2,17);
for(let x of [140,171]){r(x,85,10,10,12);r(x+1,86,8,8,30);r(x+2,86,3,7,32);r(x+4,85,1,10,8);r(x,89,10,1,8);r(x-1,95,12,2,14);}
r(151,107,18,3,10);r(150,110,20,2,9);r(136,79,2,25,14);r(182,79,2,25,14);
// Crate and a little wooden sign.
r(208,20,15,12,12);r(209,21,13,10,14);r(209,24,13,1,10);l(210,21,220,30,9);r(210,21,11,1,16);
r(232,22,3,10,12);r(226,17,16,10,12);r(227,18,14,8,15);l(230,22,237,22,12);l(235,20,237,22,12);l(235,24,237,22,12);
save(s,'environment');
// Character atlas: idle rows 0..3, walk rows 4..7, down/up/left/right.
const c=surface(192,256);const rr=c.rect,ee=c.ellipse,ll=c.line,pp=c.poly;
for(let dir=0;dir<4;dir++)for(let mode=0;mode<2;mode++)for(let f=0;f<(mode===0?4:6);f++){
 const x=f*32,y=(dir+mode*4)*32;let bob=mode===0?(f===2?1:0):(f===1||f===4?-1:0);let step=mode===1?[0,1,1,0,-1,-1][f]:0;
 ee(x+16,y+29,8,2,1);
 rr(x+11,y+24,4,4+Math.max(0,step),13);rr(x+18,y+24,4,4+Math.max(0,-step),13);rr(x+10,y+27+Math.max(0,step),5,2,12);rr(x+18,y+27+Math.max(0,-step),5,2,12);
 ee(x+16,y+22+bob,8,6,13);ee(x+16,y+21+bob,7,5,20);rr(x+12,y+21+bob,8,5,21);rr(x+13,y+19+bob,2,5,23);rr(x+19,y+19+bob,1,5,23);rr(x+15,y+23+bob,3,2,8);
 ee(x+8,y+22+bob+step,2,3,16);ee(x+24,y+22+bob-step,2,3,16);
 ee(x+16,y+13+bob,9,8,13);ee(x+16,y+13+bob,8,7,15);ee(x+14,y+12+bob,6,5,16);
 if(dir===1){rr(x+11,y+14+bob,10,3,14);rr(x+13,y+18+bob,6,1,10);}else{
 let shift=dir===2?-3:dir===3?3:0;
 ee(x+16+shift,y+16+bob,5,3,17);
 if(dir!==3)rr(x+12+shift,y+12+bob,2,3,35);
 if(dir!==2)rr(x+19+shift,y+12+bob,2,3,35);
 rr(x+15+shift,y+16+bob,2,1,13);rr(x+11+shift,y+16+bob,2,1,26);rr(x+20+shift,y+16+bob,2,1,26);
 }
 ee(x+16,y+8+bob,12,4,13);ee(x+16,y+7+bob,11,3,15);ee(x+16,y+5+bob,7,4,13);ee(x+16,y+4+bob,6,3,17);rr(x+10,y+6+bob,12,2,19);rr(x+7,y+8+bob,18,1,17);
}
save(c,'farmer');
fs.writeFileSync(path.join(root,'source','draw-in-pixelorama.gd'),`func run(api, image: Image, project, params: Dictionary):\n\tvar result = Image.create(params["width"], params["height"], false, Image.FORMAT_RGBA8)\n\tvar colors = []\n\tfor hex in params["palette"]:\n\t\tcolors.append(Color(hex))\n\tfor y in range(params["height"]):\n\t\tvar row = params["rows"][y]\n\t\tfor x in range(params["width"]):\n\t\t\tresult.set_pixel(x, y, colors[row.unicode_at(x) - 65])\n\treturn result\n`);
console.log('Built deterministic environment atlas and 40-frame four-direction farmer atlas.');
