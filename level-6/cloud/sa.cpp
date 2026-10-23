#include <bits/stdc++.h>
using namespace std;
typedef vector<array<char,6>> Prog;
struct Pat{int r,K;vector<int> mat,skirt;int W,ncell;vector<array<vector<int>,1>> dummy;
 int ringLen; vector<vector<int>> beam[7]; // beam[e][ringidx] -> cell ids
 int start[7];};
static const int DR[7]={0,0,1,1,0,-1,-1},DC[7]={0,2,1,-1,-2,-1,1};
void build(Pat&p,int r,const vector<string>&rows){
 p.r=r;p.W=4*r+1;int H=2*r+1;p.ncell=H*p.W;
 vector<char> inter(p.ncell,0);
 // interior: board chars 'O' in empty board
 for(int i=0;i<H;i++){int lead=abs(i-r);int cnt=2*r+1-lead;bool br=(i==0||i==2*r);
  for(int j=0;j<cnt;j++){bool bc=br||j==0||j==cnt-1;if(!bc)inter[i*p.W+lead+2*j]=1;}}
 vector<pair<int,int>> ring;
 for(int s=0;s<r;s++)ring.push_back({0,r+2*s});
 for(int s=0;s<r;s++)ring.push_back({s,3*r+s});
 for(int s=0;s<r;s++)ring.push_back({r+s,4*r-s});
 for(int s=0;s<r;s++)ring.push_back({2*r,3*r-2*s});
 for(int s=0;s<r;s++)ring.push_back({2*r-s,r-s});
 for(int s=0;s<r;s++)ring.push_back({r-s,s});
 p.ringLen=ring.size();
 int st[7]={0,5*r,0,r,2*r,3*r,4*r};for(int e=1;e<=6;e++)p.start[e]=st[e];
 for(int e=1;e<=6;e++){p.beam[e].resize(p.ringLen);for(int k=0;k<p.ringLen;k++){
  int rr=ring[k].first+DR[e],cc=ring[k].second+DC[e];
  while(rr>=0&&rr<H&&cc>=0&&cc<p.W&&inter[rr*p.W+cc]){p.beam[e][k].push_back(rr*p.W+cc);rr+=DR[e];cc+=DC[e];}}}
 set<int> m;for(int i=0;i<(int)rows.size();i++)for(int j=0;j<(int)rows[i].size();j++)if(rows[i][j]=='M')m.insert(i*p.W+j);
 p.mat.assign(m.begin(),m.end());
 int ox[6]={0,0,1,1,-1,-1},oy[6]={2,-2,1,-1,1,-1};set<int> sk;
 for(int c:m){int i=c/p.W,j=c%p.W;for(int d=0;d<6;d++){int a=i+ox[d],b=j+oy[d];if(a<0||a>=H||b<0||b>=p.W)continue;int id=a*p.W+b;if(inter[id]&&!m.count(id))sk.insert(id);}}
 p.skirt.assign(sk.begin(),sk.end());
}
// returns effective length (ticks to Kth submission) or -1 if shortfall; sets subs
struct Sim{vector<unsigned char> M,cnt;vector<int> touched;
 int eval(const Pat&p,const Prog&g,int&subs){
  M.assign(p.ncell,0);cnt.assign(p.ncell,0);
  int pos[7],act[7]={0};for(int e=1;e<=6;e++)pos[e]=p.start[e];
  subs=0;int L=g.size();
  for(int t=0;t<L;t++){
   for(int e=1;e<=6;e++){char c=g[t][e-1];if(c=='F')pos[e]=(pos[e]+1)%p.ringLen;else if(c=='B')pos[e]=(pos[e]+p.ringLen-1)%p.ringLen;else if(c=='T')act[e]^=1;}
   touched.clear();
   for(int e=1;e<=6;e++)if(act[e])for(int c:p.beam[e][pos[e]]){if(cnt[c]==0)touched.push_back(c);if(cnt[c]<3)cnt[c]++;}
   for(int c:touched){if(cnt[c]==2)M[c]=1;else if(cnt[c]>=3)M[c]=0;cnt[c]=0;}
   bool ok=true;for(int c:p.mat)if(!M[c]){ok=false;break;}
   if(ok)for(int c:p.skirt)if(M[c]){ok=false;break;}
   if(ok){for(int c:p.mat)M[c]=0;subs++;if(subs>=p.K)return t+1;}
  }
  return -1;}
};
static const char SYM[4]={'-','F','B','T'};
int main(int argc,char**argv){
 string inF=argv[1],refF=argv[2],outF=argv[3];long iters=atol(argv[4]);int nth=atoi(argv[5]);unsigned seed=atoi(argv[6]);
 double T0=argc>7?atof(argv[7]):0.7,T1=argc>8?atof(argv[8]):0.12;
 ifstream fi(inF);int n;fi>>n;vector<Pat> pats(n);
 for(int i=0;i<n;i++){int r,h,w,K;fi>>r>>h>>w>>K;vector<string> rows(h);for(auto&s:rows)fi>>s;build(pats[i],r,rows);pats[i].K=K;}
 ifstream fr(refF);vector<Prog> progs;{string line;Prog cur;while(getline(fr,line)){istringstream ss(line);vector<string> tk;string x;while(ss>>x)tk.push_back(x);
  if(tk.empty()){if(!cur.empty()){progs.push_back(cur);cur.clear();}continue;}array<char,6>a;for(int k=0;k<6;k++)a[k]=tk[k][0];cur.push_back(a);}
  if(!cur.empty())progs.push_back(cur);}
 vector<Prog> best=progs;atomic<int> nxt(0);atomic<long> gain(0);
 auto work=[&](int tid){mt19937_64 rng(seed*1000003+tid);Sim sim;
  while(true){int i=nxt++;if(i>=n)break;const Pat&p=pats[i];Prog cur=progs[i];int subs;
   int le=sim.eval(p,cur,subs);if(le<0){continue;}cur.resize(le);Prog bst=cur;
   auto energy=[&](const Prog&g,int&len)->double{int s;int l=sim.eval(p,g,s);double e;
    if(l>=0){len=l;e=l;}else{len=-1;e=g.size()+4.0*(p.K-s)+1;}
    int nd=0;for(auto&ln:g)for(char c:ln)nd+=(c!='-');return e+0.01*nd;};
   int curlen;double ce=energy(cur,curlen);int bestlen=cur.size();
   for(long it=0;it<iters;it++){
    double temp=T0*pow(T1/T0,(double)it/iters);
    Prog nw=cur;int L=nw.size();if(L<2)break;
    int mv=rng()%8;
    if(mv==0){int t=rng()%L;nw.erase(nw.begin()+t);}
    else if(mv==1){int c=rng()%6,t=rng()%L,d=1+rng()%3;if(t+d<L)swap(nw[t][c],nw[t+d][c]);else continue;}
    else if(mv==2){int c=rng()%6,t=rng()%L;nw[t][c]=SYM[rng()%4];}
    else if(mv==3){int t=rng()%(L-1);swap(nw[t],nw[t+1]);}
    else if(mv==4){ // merge line t into neighbor
     int t=rng()%L;int o=(rng()&1)?t+1:t-1;if(o<0||o>=L)continue;for(int c=0;c<6;c++)if(nw[t][c]!='-'&&nw[o][c]=='-')nw[o][c]=nw[t][c];nw.erase(nw.begin()+t);}
    else if(mv==5){ // delay column suffix
     int c=rng()%6,t=rng()%L;for(int k=L-1;k>t;k--)nw[k][c]=nw[k-1][c];nw[t][c]='-';}
    else if(mv==6){ // advance column suffix
     int c=rng()%6,t=rng()%L;for(int k=t;k<L-1;k++)nw[k][c]=nw[k+1][c];nw[L-1][c]='-';}
    else { // swap two cells same line / move instr to other column? swap cell between neighbor ticks across cols
     int t=rng()%L;int a=rng()%6,b=rng()%6;if(a==b)continue;swap(nw[t][a],nw[t][b]);}
    int nl;double ne=energy(nw,nl);
    if(ne<=ce||exp((ce-ne)/temp)>(rng()%1000000)/1e6){cur=nw;ce=ne;curlen=nl;
      if(nl>=0&&nl<bestlen){nw.resize(nl);bst=nw;bestlen=nl;cur=bst;ce=energy(cur,curlen);}}
   }
   int s2;if(sim.eval(p,bst,s2)>=0&&bst.size()<best[i].size())best[i]=bst;
   gain+= (long)progs[i].size()-(long)best[i].size();
  }};
 vector<thread> th;for(int t=0;t<nth;t++)th.emplace_back(work,t);for(auto&t:th)t.join();
 ofstream fo(outF);long tot=0;for(auto&g:best){for(auto&l:g){for(int k=0;k<6;k++){fo<<l[k];fo<<(k<5?' ':'\n');}}fo<<"\n";tot+=g.size();}
 fprintf(stderr,"total %ld gain %ld\n",tot,gain.load());
}
