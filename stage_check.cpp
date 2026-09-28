#include <array>
#include <cassert>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>
struct T {int w,d,n;};
struct Raw {std::string q,n; int s,w; char d;};
int main(int argc,char**argv){
    std::ifstream in(argc>1?argv[1]:"machines/RH_121_raw_named.tm");assert(in);
    std::map<std::string,int> id;std::vector<std::string> name;std::vector<Raw> rows;
    auto intern=[&](std::string s){auto it=id.find(s);if(it!=id.end())return it->second;
        int i=name.size();name.push_back(s);return id[s]=i;};
    std::string line;while(std::getline(in,line)){if(line.empty()||line[0]=='#')continue;
        Raw r;std::istringstream ss(line);ss>>r.q>>r.s>>r.w>>r.d>>r.n;rows.push_back(r);intern(r.q);intern(r.n);}
    std::vector<std::array<T,2>> tab(name.size());for(auto&x:tab)for(auto&t:x)t={0,1,-1};
    for(auto r:rows)tab[id[r.q]][r.s]={r.w,r.d=='R'?1:-1,id[r.n]};
    const int Z=1<<22;std::vector<unsigned char> tape(2*Z);int h=Z,q=id.at("0a.boot1.A"),stage=0;
    long long steps=0;bool first=true,returned=false;std::cout<<"[\n";
    while(stage<=3){
        assert(q>=0&&h>0&&h<2*Z-1&&steps<1000000000LL);
        bool entry=name[q]=="N54"&&(first||returned);
        if(entry){
            first=false;
            assert(h-Z==-3818&&tape[Z-3821]&&tape[Z-3820]);
            for(int p=0;p<Z-3821;++p)assert(!tape[p]);
            for(int p=Z-3819;p<Z+3;++p)assert(!tape[p]);
            assert(tape[Z+3]&&!tape[Z+4]);int p=Z+5;std::array<int,5> regs;
            for(int i=0;i<5;++i){int r=-1;while(tape[p]){++r;++p;}assert(r>=0);regs[i]=r;++p;}
            assert(regs[0]==stage&&regs[1]==0&&regs[2]==0&&regs[3]==0&&regs[4]==0);
            std::cout<<(stage?",\n":"")<<"  {\"completed_endpoint\":"<<(stage?stage+1:0)<<",\"steps\":"<<steps<<",\"m\":"<<regs[0]<<"}";
            ++stage;if(stage>3)break;
        }
        returned=name[q]=="5.root.2"&&tape[h]==1;
        auto t=tab[q][tape[h]];tape[h]=t.w;h+=t.d;q=t.n;++steps;
    }
    std::cout<<"\n]\n";
}
