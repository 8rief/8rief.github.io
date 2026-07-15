#include <algorithm>
#include <cassert>
#include <iostream>
#include <queue>
#include <random>
#include <vector>

class LCA { int n, LOG; std::vector<std::vector<int>> up, g; std::vector<int> depth; public:
    explicit LCA(const std::vector<int>& parent){ n=parent.size(); LOG=1; while((1<<LOG)<=n) ++LOG; up.assign(LOG,std::vector<int>(n)); g.assign(n,{}); depth.assign(n,0); int root=0; for(int v=0; v<n; ++v){ if(parent[v]==-1) root=v; else g[parent[v]].push_back(v); } dfs(root,root); }
    void dfs(int u,int p){ up[0][u]=p; for(int k=1;k<LOG;++k) up[k][u]=up[k-1][up[k-1][u]]; for(int v:g[u]){ depth[v]=depth[u]+1; dfs(v,u);} }
    int lift(int u,int d) const { for(int k=0; d; ++k,d>>=1) if(d&1) u=up[k][u]; return u; }
    int lca(int a,int b) const { if(depth[a]<depth[b]) std::swap(a,b); a=lift(a,depth[a]-depth[b]); if(a==b) return a; for(int k=LOG-1;k>=0;--k) if(up[k][a]!=up[k][b]){ a=up[k][a]; b=up[k][b]; } return up[0][a]; }
    int dist(int a,int b) const { int c=lca(a,b); return depth[a]+depth[b]-2*depth[c]; }
};
int naive_lca(const std::vector<int>& parent,int a,int b){ std::vector<int> seen(parent.size()); while(a!=-1){ seen[a]=1; a=parent[a]; } while(!seen[b]) b=parent[b]; return b; }
void run_tests(){ std::vector<int> p{-1,0,0,1,1,2,2,3}; LCA l(p); assert(l.lca(4,7)==1); assert(l.lca(5,6)==2); assert(l.dist(7,6)==5); std::mt19937 rng(20260625); std::uniform_int_distribution<int> n_dist(1,200); for(int round=0; round<200; ++round){ int n=n_dist(rng); std::vector<int> par(n,-1); for(int v=1; v<n; ++v){ std::uniform_int_distribution<int> pd(0,v-1); par[v]=pd(rng); } LCA tree(par); for(int q=0;q<300;++q){ std::uniform_int_distribution<int> node(0,n-1); int a=node(rng), b=node(rng); assert(tree.lca(a,b)==naive_lca(par,a,b)); }} }
void run_demo(){ std::vector<int> p{-1,0,0,1,1,2,2,3}; LCA l(p); std::cout<<"lca(4,7)="<<l.lca(4,7)<<"\n"; std::cout<<"lca(5,6)="<<l.lca(5,6)<<"\n"; std::cout<<"dist(7,6)="<<l.dist(7,6)<<"\n"; }
int main(int argc,char** argv){ if(argc>1&&std::string(argv[1])=="--test"){ run_tests(); std::cout<<"binary-lifting LCA tests passed\n"; return 0;} run_demo(); }
