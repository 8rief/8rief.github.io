#include <algorithm>
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <optional>
#include <string>
#include <vector>

long long gcd_ll(long long a,long long b){ a=std::llabs(a); b=std::llabs(b); while(b){ long long t=a%b; a=b; b=t; } return a; }
std::vector<int> sieve(int n){ std::vector<int> primes; std::vector<bool> comp(n+1); for(int i=2;i<=n;++i){ if(!comp[i]) primes.push_back(i); for(int p:primes){ if((long long)i*p>n) break; comp[i*p]=true; if(i%p==0) break; } } return primes; }
long long norm_mod(long long a,long long mod){ a%=mod; if(a<0) a+=mod; return a; }
long long add_mod(long long a,long long b,long long mod){ return a>=mod-b ? a-(mod-b) : a+b; }
long long mul_mod(long long a,long long b,long long mod){ long long res=0; a=norm_mod(a,mod); b=norm_mod(b,mod); while(b){ if(b&1) res=add_mod(res,a,mod); b>>=1; if(b) a=add_mod(a,a,mod); } return res; }
long long mod_pow(long long a,long long e,long long mod){ long long r=1%mod; a=norm_mod(a,mod); while(e){ if(e&1) r=mul_mod(r,a,mod); a=mul_mod(a,a,mod); e>>=1; } return r; }
long long exgcd(long long a,long long b,long long& x,long long& y){ if(!b){ x=1;y=0;return a;} long long x1,y1,g=exgcd(b,a%b,x1,y1); x=y1; y=x1-(a/b)*y1; return g; }
std::optional<long long> mod_inverse(long long a,long long mod){ long long x,y,g=exgcd(a,mod,x,y); if(g!=1) return std::nullopt; x%=mod; if(x<0)x+=mod; return x; }
std::optional<std::pair<long long,long long>> crt(long long a1,long long m1,long long a2,long long m2){ long long x,y,g=exgcd(m1,m2,x,y); if((a2-a1)%g) return std::nullopt; long long merged_mod=m2/g; long long k=mul_mod((a2-a1)/g,x,merged_mod); long long l=m1/g*m2; long long ans=norm_mod(norm_mod(a1,l)+mul_mod(k,m1,l),l); return std::pair{ans,l}; }
void run_tests(){ for(long long a=-50;a<=50;++a) for(long long b=-50;b<=50;++b) assert(gcd_ll(a,b)==std::gcd(a,b)); assert((sieve(30)==std::vector<int>{2,3,5,7,11,13,17,19,23,29})); assert(mod_pow(2,10,1000)==24); assert(mod_inverse(3,11).value()==4); assert(!mod_inverse(6,9)); auto c=crt(2,3,3,5); assert(c && c->first==8 && c->second==15); assert(!crt(1,2,0,4)); for(int a=1;a<17;++a) if(std::gcd(a,17)==1) assert((a*mod_inverse(a,17).value())%17==1); }
void run_demo(){ std::cout<<"gcd(84,30)="<<gcd_ll(84,30)<<"\n"; std::cout<<"primes<=30: "; for(int p:sieve(30)) std::cout<<p<<' '; std::cout<<"\n2^10 mod 1000="<<mod_pow(2,10,1000)<<"\n"; std::cout<<"inverse of 3 mod 11="<<mod_inverse(3,11).value()<<"\n"; auto c=crt(2,3,3,5); std::cout<<"CRT x=2 mod 3, x=3 mod 5 -> x="<<c->first<<" mod "<<c->second<<"\n"; }
int main(int argc,char** argv){ if(argc>1&&std::string(argv[1])=="--test"){ run_tests(); std::cout<<"number-theory tests passed\n"; return 0;} run_demo(); }
