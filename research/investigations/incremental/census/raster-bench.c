// Container-measurable proxies for the shell side of the last mile (CPU only; no GPU here).
// A: scene index query + reflow shift, absolute y-sorted array vs relative-offset 16-ary tree.
// B: glyph blit throughput (CPU proxy for atlas-quad cost), pixel blit/scroll copy bandwidth.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static double now(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec*1e-6;}
static uint64_t rs=88172645463325252ull;
static uint32_t rnd(){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return (uint32_t)(rs>>11);}
typedef struct{float x,y,w,h;}R;
#define F 16
// ---------- A ----------
static int N;
static R*ab;            // absolute bounds, y-sorted by top (flow order)
static float*maxbot;    // prefix max of bottoms (monotone) for binary-search-pruned scan
// tree: levels[0]=leaves. Node i at level L covers children [i*F, i*F+F). Each node stores
// offy relative to its parent's origin (leaf: local y of chunk) and local bounds (y0,y1 in own frame).
typedef struct{float oy; float x0,x1; float y0,y1;}Node; // y0,y1 in parent frame (== oy+extent)
static Node*lv[8]; static int cnt[8]; static int depth;
static void build_tree(){
  cnt[0]=N; lv[0]=malloc(sizeof(Node)*N);
  for(int i=0;i<N;i++){lv[0][i].oy=ab[i].y;lv[0][i].x0=ab[i].x;lv[0][i].x1=ab[i].x+ab[i].w;lv[0][i].y0=ab[i].y;lv[0][i].y1=ab[i].y+ab[i].h;}
  depth=1;
  while(cnt[depth-1]>1){
    int c=(cnt[depth-1]+F-1)/F; cnt[depth]=c; lv[depth]=malloc(sizeof(Node)*c);
    for(int i=0;i<c;i++){
      Node*p=&lv[depth][i]; int a=i*F,b=a+F; if(b>cnt[depth-1])b=cnt[depth-1];
      float y0=1e30,y1=-1e30,x0=1e30,x1=-1e30;
      for(int k=a;k<b;k++){Node*q=&lv[depth-1][k]; if(q->y0<y0)y0=q->y0; if(q->y1>y1)y1=q->y1; if(q->x0<x0)x0=q->x0; if(q->x1>x1)x1=q->x1;}
      // make children relative to the group's origin = y0
      for(int k=a;k<b;k++){Node*q=&lv[depth-1][k]; q->oy-=y0; q->y0-=y0; q->y1-=y0;}
      p->oy=y0;p->y0=y0;p->y1=y1;p->x0=x0;p->x1=x1;
    }
    depth++;
  }
}
static int qout[1<<20]; static int qn;
static void q_rec(int L,int i,float ay,float qx0,float qy0,float qx1,float qy1){
  // node i at level L has parent-frame y0,y1 ; ay = absolute origin of parent frame
  Node*n=&lv[L][i]; float y0=ay+n->y0,y1=ay+n->y1;
  if(y1<qy0||y0>qy1||n->x1<qx0||n->x0>qx1) return;
  if(L==0){qout[qn++]=i;return;}
  float oy=ay+n->oy; // this node's own origin = its parent-frame y0 (stored oy==y0 at build); children relative to it
  int a=i*F,b=a+F; if(b>cnt[L-1])b=cnt[L-1];
  for(int k=a;k<b;k++) q_rec(L-1,k,oy,qx0,qy0,qx1,qy1);
}
static int query_tree(float qx0,float qy0,float qx1,float qy1){
  qn=0; q_rec(depth-1,0,0,qx0,qy0,qx1,qy1); return qn;}
static int query_abs(float qx0,float qy0,float qx1,float qy1){
  // binary search first item whose prefix-max bottom >= qy0, scan while top<=qy1
  int lo=0,hi=N; while(lo<hi){int m=(lo+hi)/2; if(maxbot[m]<qy0)lo=m+1; else hi=m;}
  qn=0; for(int i=lo;i<N&&ab[i].y<=qy1;i++){ if(ab[i].y+ab[i].h>=qy0&&ab[i].x<=qx1&&ab[i].x+ab[i].w>=qx0) qout[qn++]=i;} return qn;}
static int query_lin(float qx0,float qy0,float qx1,float qy1){
  qn=0; for(int i=0;i<N;i++) if(ab[i].y+ab[i].h>=qy0&&ab[i].y<=qy1&&ab[i].x+ab[i].w>=qx0&&ab[i].x<=qx1) qout[qn++]=i; return qn;}
// reflow: insert dy of height before chunk k
static void shift_abs(int k,float dy){ for(int i=k;i<N;i++){ab[i].y+=dy;maxbot[i]+=dy;} }
static void shift_tree(int k,float dy){
  // add dy to chunk k.. and all later siblings at each level along path; then fix ancestor extents.
  int i=k;
  for(int L=0;L<depth-1;L++){
    int g=i/F, end=(g+1)*F; if(end>cnt[L])end=cnt[L];
    for(int j=i;j<end;j++){lv[L][j].oy+=dy;lv[L][j].y0+=dy;lv[L][j].y1+=dy;}
    // parent's extent grows
    Node*p=&lv[L+1][g]; p->y1+=dy; // frame: p.y1 in grandparent frame; children shifted inside, extent grows by dy
    i=g+1; // later siblings of the parent in the next level shift too (their origins move)
    if(L+1==depth-1) break;
    // parent itself keeps y0; siblings after it shift: handled at next iteration starting at index g+1
  }
}
static void benchA(){
  N=250000; ab=malloc(sizeof(R)*N); maxbot=malloc(4*N);
  float y=0; for(int i=0;i<N;i++){ // flow of line boxes (mostly), with some tall boxes (backgrounds)
    float h=(rnd()%50==0)? 40+rnd()%400 : 20; float x=(rnd()%8)*20, w=300+rnd()%900;
    ab[i]=(R){x,y,w,h}; y+=(h>30? 0.0f:h)+ (h>30? 8.0f:0.0f); if(h<=30) ; else y+=h*0.0f; }
  // y is nondecreasing by construction (tall boxes overlap following lines)
  float mb=0; for(int i=0;i<N;i++){float b=ab[i].y+ab[i].h; if(b>mb)mb=b; maxbot[i]=mb;}
  double t=now(); build_tree(); printf("A: N=%d chunks, page height %.0f px, tree depth %d, build %.1f ms\n",N,ab[N-1].y,depth,now()-t);
  int Q=2000; float H=ab[N-1].y; double tl=0,ta=0,tt=0; long hl=0,ha=0,ht=0;
  for(int pass=0;pass<2;pass++){
    float qw= pass? 300:1920, qh= pass? 40:1080;
    tl=ta=tt=0;hl=ha=ht=0;
    for(int q=0;q<Q;q++){ float qy=(rnd()/4294967296.0f)*(H-qh), qx=(rnd()%200); double a=now();
      int c1=query_abs(qx,qy,qx+qw,qy+qh); double b=now(); int c2=query_tree(qx,qy,qx+qw,qy+qh); double c=now();
      ta+=b-a; tt+=c-b; ha+=c1; ht+=c2; if(q<50){double d=now(); int c3=query_lin(qx,qy,qx+qw,qy+qh); tl+=now()-d; hl+=c3; if(c3!=c1||c3!=c2) printf("MISMATCH %d %d %d\n",c1,c2,c3);} }
    printf("A: query %.0fx%.0f: hits/query %.0f | linear %.1f us | y-sorted+bsearch %.2f us | 16-ary tree %.2f us\n",qw,qh,(double)ha/Q,tl/50*1e3,ta/Q*1e3,tt/Q*1e3);
  }
  // reflow shift near top (worst case): everything below moves
  int k=N/50; double s=now(); for(int r=0;r<200;r++) shift_abs(k,0.5f); double sa=(now()-s)/200;
  s=now(); for(int r=0;r<200;r++) shift_tree(k,0.5f); double st=(now()-s)/200;
  { int bad=0; for(int q=0;q<500;q++){ float qy=(rnd()/4294967296.0f)*(ab[N-1].y-1080), qx=rnd()%200; int c1=query_abs(qx,qy,qx+1920,qy+1080); static int s1[4096],s2[4096]; memcpy(s1,qout,4*c1); int c2=query_tree(qx,qy,qx+1920,qy+1080); memcpy(s2,qout,4*c2); int c3=query_lin(qx,qy,qx+1920,qy+1080); int ok=(c1==c2&&c1==c3&&!memcmp(s1,s2,4*c1)&&!memcmp(s1,qout,4*c1)); if(!ok)bad++; } printf("A: post-shift tree/abs/linear agreement: %d mismatches of 500 queries\n",bad);}
  printf("A: reflow shift of ~%d later chunks: absolute rewrite %.1f us (%.1f MB written) | relative-offset tree %.3f us (%d node writes)\n",N-k,sa*1e3,(N-k)*20.0/1e6,st*1e3,F*(depth-1));
}
// ---------- B ----------
static void benchB(){
  int W=1920,H=1080; uint32_t*fb=calloc(W*H,4); uint32_t*fb2=calloc(W*H,4);
  // glyph atlas: 4096 glyphs of 10x14 8-bit coverage
  int GW=10,GH=14,NG=4096; uint8_t*atl=malloc(GW*GH*NG); for(int i=0;i<GW*GH*NG;i++)atl[i]=rnd()&255;
  int nglyph=20000; int*gx=malloc(4*nglyph),*gy=malloc(4*nglyph),*gi=malloc(4*nglyph);
  for(int i=0;i<nglyph;i++){gx[i]=rnd()%(W-GW);gy[i]=rnd()%(H-GH);gi[i]=rnd()%NG;}
  for(int rep=0;rep<3;rep++){ double t=now();
    for(int i=0;i<nglyph;i++){ uint8_t*m=atl+gi[i]*GW*GH; for(int r=0;r<GH;r++){uint32_t*d=fb+(gy[i]+r)*W+gx[i]; const uint8_t*mr=m+r*GW;
      for(int c=0;c<GW;c++){ uint32_t a=mr[c]; uint32_t o=d[c]; // dark text on light bg, premultiplied-ish lerp per channel
        uint32_t k=(255-a)*257u; uint32_t rr=(((o>>16)&255)*k)>>16, gg=(((o>>8)&255)*k)>>16, bb=((o&255)*k)>>16; d[c]=0xff000000|(rr<<16)|(gg<<8)|bb; } } }
    double e=now()-t; if(rep==2)printf("B: scalar CPU glyph blit: %d glyphs (%dx%d) in %.2f ms = %.0f ns/glyph = %.2f Gpx/s\n",nglyph,GW,GH,e,e*1e6/nglyph,(double)nglyph*GW*GH/e/1e6);}
  for(int rep=0;rep<3;rep++){ double t=now(); memcpy(fb2,fb,(size_t)W*H*4); double e=now()-t; if(rep==2)printf("B: full 1080p frame memcpy (8.3 MB) %.2f ms = %.1f GB/s\n",e,W*H*4/e/1e6);}
  for(int rep=0;rep<3;rep++){ double t=now(); memmove(fb2,fb2+22*W,(size_t)(H-22)*W*4); double e=now()-t; if(rep==2)printf("B: scroll-by-memmove 1080p by 22 rows %.2f ms\n",e);}
}
int main(){benchA();benchB();return 0;}
