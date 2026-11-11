// Deterministic recording-only triangle renderer. Native KernelCAD vertex positions
// and normals are transformed at each exact sample time; no frame interpolation.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <omp.h>
using std::vector; using std::string;
struct V { float x=0,y=0,z=0; V(){} V(float a,float b,float c):x(a),y(b),z(c){} V operator+(V b)const{return {x+b.x,y+b.y,z+b.z};} V operator-(V b)const{return {x-b.x,y-b.y,z-b.z};} V operator*(float a)const{return {x*a,y*a,z*a};} };
float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;} V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};} V norm(V a){return a*(1/std::sqrt(std::max(1e-15f,dot(a,a))));}
struct Vert { V p,n;float u,v;};
struct Part {string name;V color;float metal;uint32_t kind;vector<Vert>vs;vector<uint32_t>idx;};
struct PV{float x,y,z; V p,n;float u,v;};
struct Cam{V pos,target,right,up,forward;float height;int w,h;void init(){forward=norm(target-pos);right=norm(cross(forward,{0,1,0}));up=norm(cross(right,forward));} PV project(Vert v){V d=v.p-pos;return {w*.5f+dot(d,right)*h/height,h*.5f-dot(d,up)*h/height,dot(d,forward),v.p,v.n,v.u,v.v};}};
template<class T>T read(std::ifstream&f){T t;f.read((char*)&t,sizeof t);return t;}
vector<Part> load(const string&path){std::ifstream f(path,std::ios::binary);char magic[8];f.read(magic,8);if(std::string(magic,8)!="KCADCPU1")throw std::runtime_error("scene format");auto count=read<uint32_t>(f);vector<Part>ps;for(uint32_t i=0;i<count;i++){Part p;auto n=read<uint32_t>(f);p.name.resize(n);f.read(p.name.data(),n);p.color=read<V>(f);p.metal=read<float>(f);p.kind=read<uint32_t>(f);n=read<uint32_t>(f);auto ni=read<uint32_t>(f);p.vs.resize(n);p.idx.resize(ni);f.read((char*)p.vs.data(),n*sizeof(Vert));f.read((char*)p.idx.data(),ni*4);ps.push_back(std::move(p));}return ps;}
float smooth(float u){u=std::clamp(u,0.f,1.f);return u*u*u*(u*(u*6-15)+10);} float explode(float t){return t<1.5?0:t<5?smooth((t-1.5)/3.5):t<8.5?1:t<12?1-smooth((t-8.5)/3.5):0;}
float focus(float t){return t<5?0:t<6.1?smooth((t-5)/1.1):t<8.5?1:t<10?1-smooth((t-8.5)/1.5):0;}
bool starts(const string&a,const string&b){return a.rfind(b,0)==0;} bool ends(const string&a,const string&b){return a.size()>=b.size()&&a.substr(a.size()-b.size())==b;}
V ry(V p,float a){return {std::cos(a)*p.x+std::sin(a)*p.z,p.y,-std::sin(a)*p.x+std::cos(a)*p.z};}
float control[5]={0,0,0,0,0};
Vert transform(Vert v,const string&name,float e,float f){V off;
 if(name=="dpad"){V pivot={-24,54,25.9};float angle=(control[0]-control[1])*.055f;v.p=ry(v.p-pivot,angle)+pivot+V{0,0,-.4f*std::max(control[0],control[1])};v.n=ry(v.n,angle);}
 if(name=="btn-a")v.p.z-=control[2]*.72f;
 if(name=="btn-b")v.p.z-=control[3]*.72f;
 if(name=="btn-start")v.p.z-=control[4]*.6f;
 if(name=="rear-shell")off={-122-65*f,0,-40};
 else if(name=="battery-service-cover")off={-150-65*f,0,-65};
 else if(name=="front-shell")off={120+90*f,0,60};
 else if(name=="display-bezel")off={120+90*f,0,75};
 else if(name=="dpad"||name=="btn-a"||name=="btn-b"||name=="btn-start"||name=="btn-select")off={120+90*f,0,77};
 else if(name=="button-support")off={58+100*f,0,30};
 else if(starts(name,"lcd1")||name=="LCD_FRAMEBUFFER")off={58+80*f,2,48};
 else if(name=="battery-reserved-envelope")off={-111-65*f,0,-22};
 else if(name=="speaker-reserved-envelope")off={83+90*f,0,45};
 else if(starts(name,"case-"))off=ends(name,"screw")?V{105+90*f,0,55}:V{-115-65*f,0,-31};
 else if(starts(name,"pcb-mount-"))off=ends(name,"screw")?V{0,0,8}:V{0,0,-8};
 else if(starts(name,"J1"))off={0,0,8};
 if(starts(name,"A1-")||name=="usb-external-plug-envelope") {V pivot={0,111,9.5};v.p=ry(v.p-pivot,3.14159265f*e)+pivot+V{-64*e,8*e,14*e};v.n=ry(v.n,3.14159265f*e);}
 else v.p=v.p+off*e;
 return v;
}
Cam camera(float t,int w,int h){
 static const float keys[][8]={{0,120,108,335,0,81,12,194},{1.5,98,105,345,0,81,12,194},{5,150,143,390,0,81,15,228},{6.3,62,129,375,-26,85,11,162},{8.5,-13,130,350,-57,112,13,96},{12,78,104,360,0,81,15,190},{16,48,96,370,0,82,18,184},{18,25,116,370,0,96,18,120}};
 float p[7];int seg=0;while(seg<6&&t>keys[seg+1][0])seg++;float u=smooth((t-keys[seg][0])/(keys[seg+1][0]-keys[seg][0]));for(int j=0;j<7;j++)p[j]=keys[seg][j+1]+u*(keys[seg+1][j+1]-keys[seg][j+1]);Cam c{{p[0],p[1],p[2]},{p[3],p[4],p[5]}, {},{},{},p[6],w,h};c.init();return c;
}
float edge(float ax,float ay,float bx,float by,float px,float py){return (px-ax)*(by-ay)-(py-ay)*(bx-ax);}
struct Triangle {PV a,b,c;V color;float metal;uint32_t kind;int minx,maxx,miny,maxy;float invarea;};
vector<Triangle> project(const vector<Part>&ps,Cam&cam,float t){vector<Triangle>out;out.reserve(90000);float e=explode(t),f=focus(t);for(const auto&p:ps){vector<PV>vv;vv.reserve(p.vs.size());for(auto v:p.vs)vv.push_back(cam.project(transform(v,p.name,e,f)));for(size_t i=0;i<p.idx.size();i+=3){PV a=vv[p.idx[i]],b=vv[p.idx[i+1]],c=vv[p.idx[i+2]];float ar=edge(a.x,a.y,b.x,b.y,c.x,c.y);if(std::abs(ar)<.00001)continue;Triangle tri{a,b,c,p.color,p.metal,p.kind};tri.minx=std::max(0,(int)std::floor(std::min({a.x,b.x,c.x})));tri.maxx=std::min(cam.w-1,(int)std::ceil(std::max({a.x,b.x,c.x})));tri.miny=std::max(0,(int)std::floor(std::min({a.y,b.y,c.y})));tri.maxy=std::min(cam.h-1,(int)std::ceil(std::max({a.y,b.y,c.y})));tri.invarea=1/ar;if(tri.minx<=tri.maxx&&tri.miny<=tri.maxy)out.push_back(tri);}}return out;}
vector<float> shadow(const vector<Triangle>&tris,int w,int h){vector<float>dep(w*h,1e10);for(const auto&tr:tris){for(int y=tr.miny;y<=tr.maxy;y++)for(int x=tr.minx;x<=tr.maxx;x++){float a=edge(tr.b.x,tr.b.y,tr.c.x,tr.c.y,x+.5,y+.5)*tr.invarea;float b=edge(tr.c.x,tr.c.y,tr.a.x,tr.a.y,x+.5,y+.5)*tr.invarea;float c=1-a-b;if(a<0||b<0||c<0)continue;float z=a*tr.a.z+b*tr.b.z+c*tr.c.z;int i=y*w+x;if(z<dep[i])dep[i]=z;}}return dep;}
struct Texture{int w=0,h=0;vector<uint8_t>data;V sample(float u,float v){if(w==0)return {.51,.62,.35};int x=std::clamp((int)(u*w),0,w-1),y=std::clamp((int)(v*h),0,h-1);int i=(y*w+x)*3;return {data[i]/255.f,data[i+1]/255.f,data[i+2]/255.f};}};
Texture readPPM(const string&path){Texture r;std::ifstream f(path,std::ios::binary);if(!f)return r;string s;int m;f>>s>>r.w>>r.h>>m;f.get();if(s!="P6")return {};r.data.resize(r.w*r.h*3);f.read((char*)r.data.data(),r.data.size());return r;}
V lamp=norm({-.6f,.85f,1.f}),fill=norm({.8f,.25f,.7f});
void raster(const vector<Triangle>&tris,Cam&cam,Cam&light,const vector<float>&shad,Texture&lcd,Texture&controller,float t,vector<uint8_t>&rgb){
 int w=cam.w,h=cam.h;vector<float>depth(w*h,1e10);vector<V>col(w*h);
 #pragma omp parallel for schedule(static)
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){float dx=(x-w*.5f)/w,dy=(y-h*.5f)/h;float vign=dx*dx+dy*dy;col[y*w+x]={.943f-.04f*vign,.954f-.04f*vign,.964f-.038f*vign};}
 // Each worker owns disjoint horizontal tiles. This makes z-buffer writes race-free.
 #pragma omp parallel for schedule(dynamic,1)
 for(int tile=0;tile<(h+31)/32;tile++){
  int top=tile*32,bottom=std::min(h-1,top+31);
  for(const auto&tr:tris){int ya=std::max(top,tr.miny),yb=std::min(bottom,tr.maxy);if(ya>yb)continue;
   for(int y=ya;y<=yb;y++)for(int x=tr.minx;x<=tr.maxx;x++){
    float a=edge(tr.b.x,tr.b.y,tr.c.x,tr.c.y,x+.5f,y+.5f)*tr.invarea,b=edge(tr.c.x,tr.c.y,tr.a.x,tr.a.y,x+.5f,y+.5f)*tr.invarea,c=1-a-b;
    if(a<0||b<0||c<0)continue;float z=a*tr.a.z+b*tr.b.z+c*tr.c.z;int i=y*w+x;if(z>=depth[i])continue;depth[i]=z;
    V n=norm(tr.a.n*a+tr.b.n*b+tr.c.n*c),p=tr.a.p*a+tr.b.p*b+tr.c.p*c,base=tr.color;
    float u=tr.a.u*a+tr.b.u*b+tr.c.u*c,v=tr.a.v*a+tr.b.v*b+tr.c.v*c;
    if(tr.kind==1){base=lcd.sample(u,v);col[i]=base;continue;}
    if(tr.kind==3&&controller.w){col[i]=controller.sample(u,v);continue;}
    float shade=1;PV q=light.project({p,{0,0,0},0,0});int sx=(int)q.x,sy=(int)q.y;
    if(sx>1&&sx<light.w-2&&sy>1&&sy<light.h-2){float vis=0;for(int oy=-1;oy<=1;oy++)for(int ox=-1;ox<=1;ox++)vis+=(q.z-1.15f>shad[(sy+oy)*light.w+sx+ox])?.42f:1.f;shade=vis/9;}
    float diffuse=.48f+.39f*std::max(0.f,dot(n,lamp))*shade+.17f*std::max(0.f,dot(n,fill));
    float spec=std::pow(std::max(0.f,dot(n,norm(lamp-cam.forward))),48)*(.055f+.12f*tr.metal)*shade;
    if(tr.kind==2){float selected=smooth((t-5.2)/.6)*(1-smooth((t-8.2)/.6));base=base*(1-selected)+V{.025f,.75f,.9f}*selected;diffuse+=selected*.16f;}
    col[i]={base.x*diffuse+spec,base.y*diffuse+spec,base.z*diffuse+spec};
   }
  }
 }
 rgb.resize(w*h*3);
 #pragma omp parallel for schedule(static)
 for(int i=0;i<w*h;i++){rgb[i*3]=std::clamp((int)(col[i].x*255),0,255);rgb[i*3+1]=std::clamp((int)(col[i].y*255),0,255);rgb[i*3+2]=std::clamp((int)(col[i].z*255),0,255);}
}
int main(int argc,char**argv){if(argc<2){std::cerr<<"render_cpu scene.bin [start end width height ss lcd.raw lcdw lcdh]\n";return 1;}string path=argv[1];int start=argc>2?atoi(argv[2]):0,end=argc>3?atoi(argv[3]):start+1,w=argc>4?atoi(argv[4]):1920,h=argc>5?atoi(argv[5]):1080,ss=argc>6?atoi(argv[6]):2;auto ps=load(path);omp_set_num_threads(8);std::ifstream lcdfile,controlsfile(path.substr(0,path.find_last_of('/'))+"/controls.bin",std::ios::binary);Texture lcd,controller=readPPM(path.substr(0,path.find_last_of('/'))+"/controller.ppm");if(argc>7){lcdfile.open(argv[7],std::ios::binary);lcd.w=argc>8?atoi(argv[8]):320;lcd.h=argc>9?atoi(argv[9]):240;lcd.data.resize(lcd.w*lcd.h*3);}Cam light{{-260,330,390},{0,80,0},{},{},{},400,1024,1024};light.init();for(int f=start;f<end;f++){auto begin=std::chrono::steady_clock::now();if(controlsfile){controlsfile.seekg((std::streamoff)f*sizeof control);controlsfile.read((char*)control,sizeof control);}float t=f/60.f;Cam cam=camera(t,w*ss,h*ss);auto tris=project(ps,cam,t),stris=project(ps,light,t);auto sd=shadow(stris,light.w,light.h);if(lcdfile){lcdfile.seekg((std::streamoff)f*lcd.data.size());lcdfile.read((char*)lcd.data.data(),lcd.data.size());}vector<uint8_t>big,rgb(w*h*3);raster(tris,cam,light,sd,lcd,controller,t,big);
 #pragma omp parallel for schedule(static)
 for(int y=0;y<h;y++)for(int x=0;x<w;x++)for(int c=0;c<3;c++){int sum=0;for(int dy=0;dy<ss;dy++)for(int dx=0;dx<ss;dx++)sum+=big[((y*ss+dy)*w*ss+x*ss+dx)*3+c];rgb[(y*w+x)*3+c]=sum/(ss*ss);}
 std::printf("P6\n%d %d\n255\n",w,h);std::fwrite(rgb.data(),1,rgb.size(),stdout);std::fflush(stdout);auto dt=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();std::cerr<<"FRAME "<<f<<" "<<dt<<"s\n";
 }return 0;}
