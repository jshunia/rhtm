#include <array>
#include <cassert>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

struct Transition { int write, dir, next; };
struct Raw { std::string q, next; int read, write; char dir; };

int main(int argc, char** argv) {
    const char* path = argc > 1 ? argv[1] : "machines/RH_121_raw_named.tm";
    std::ifstream in(path);
    if (!in) return 2;

    std::map<std::string,int> id;
    std::vector<std::string> name;
    std::vector<Raw> raw;
    std::string line, start;
    auto intern = [&](const std::string& s) {
        auto it=id.find(s); if (it!=id.end()) return it->second;
        int k=(int)id.size(); id[s]=k; name.push_back(s); return k;
    };

    while (std::getline(in,line)) {
        if (line.rfind("#! start",0)==0) {
            std::istringstream ss(line); std::string a,b; ss>>a>>b>>start;
            continue;
        }
        if (line.empty() || line[0]=='#') continue;
        Raw r; std::istringstream ss(line);
        ss>>r.q>>r.read>>r.write>>r.dir>>r.next;
        raw.push_back(r); intern(r.q); if (r.next!="H") intern(r.next);
    }
    std::vector<std::array<Transition,2>> table(id.size());
    for (const auto& r:raw)
        table[id[r.q]][r.read]={r.write,r.dir=='R'?1:-1,
                                r.next=="H"?-1:id[r.next]};

    std::unordered_set<long long> ones;
    long long head=0, steps=0;
    int state=id.at(start);
    while (name[state].empty() || name[state][0] != 'N') {
        int read=ones.count(head)?1:0;
        auto t=table[state][read];
        if (t.write) ones.insert(head); else ones.erase(head);
        head += t.dir; state=t.next; ++steps;
        assert(state>=0);
    }

    assert(steps==89775610LL);
    assert(name[state]=="N54");
    assert(head==-3818);
    std::unordered_set<long long> expected={-3821,-3820};
    for (long long p=3;p<=3821;p+=2) expected.insert(p);
    assert(ones==expected);
    std::cout << "bootstrap certificate verified\n";
}
