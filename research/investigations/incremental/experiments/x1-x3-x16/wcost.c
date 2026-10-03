// Per-write cost of the two offset schemes' writes (X3): a rewrite in the context-relative scheme is a
// read-modify-write of one box record's offset; a node write in the summary tree recomputes one node
// from its two children.  Box records are 64 bytes (stride), hot and cold variants.
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
typedef struct { float x, y, w, h; char pad[48]; } Rec;
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
int main(void){
  int Ns[] = {1024, 4096, 20919, 117137};
  for (int ni=0; ni<4; ni++){
    int N = Ns[ni];
    Rec *r = aligned_alloc(64, (size_t)N*sizeof(Rec)); memset(r,0,(size_t)N*sizeof(Rec));
    int M=1; while(M<N) M<<=1;
    float *tree = calloc(2*M,sizeof(float));
    // flat: shift k consecutive records
    int k = N/2; long reps = 20000000L/k+1; double s=0;
    double t0=now();
    for(long q=0;q<reps;q++){ int st=(int)((q*7919)%(N-k+1)); float d=(float)(q&3)+1; for(int i=st;i<st+k;i++) r[i].y+=d; }
    double t1=now(); double flat=(t1-t0)/((double)reps*k);
    // tree: set leaf, recompute path
    long reps2=20000000L/ (int)__builtin_ctz(M)+1; int lg=__builtin_ctz(M);
    t0=now();
    for(long q=0;q<reps2;q++){ int leaf=(int)((q*2654435761u)%N); int p=M+leaf; tree[p]=(float)(q&7); p>>=1; while(p>=1){ tree[p]=tree[2*p]+tree[2*p+1]; p>>=1; } }
    t1=now(); double node=(t1-t0)/((double)reps2*lg);
    for(int i=0;i<2*M;i++) s+=tree[i]; for(int i=0;i<N;i++) s+=r[i].y;
    printf("N=%d levels=%d flat_rewrite_ns=%.3f tree_node_write_ns=%.3f ratio=%.1f (chk %g)\n",N,lg,flat*1e9,node*1e9,node/flat,s);
    free(r); free(tree);
  }
  return 0;
}
