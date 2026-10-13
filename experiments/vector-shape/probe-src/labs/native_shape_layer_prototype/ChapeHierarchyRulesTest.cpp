#include "ChapeHierarchyRules.h"
#include <cstdio>
#define CHECK(x) do {if(!(x)){std::fprintf(stderr,"FAIL %s @%d\n",#x,__LINE__);return 2;}} while(0)
#include <iostream>
#include <string>
#include <vector>
using namespace chape;
int main(){
    Hierarchy graph;
    CHECK(graph.registerType({"CNL:Stack",{"CNL:Path","CNL:Reverse"},true,Order::Forward})==Result::Ok);
    CHECK(graph.registerType({"CNL:Reverse",{"CNL:Path"},true,Order::Reverse})==Result::Ok);
    CHECK(graph.registerType({"CNL:Path",{},false,Order::Forward})==Result::Ok);
    CHECK(graph.registerType({"CNL:Blur",{},false,Order::Forward})==Result::Ok);
    CHECK(graph.registerType({"CNL:Path",{},false,Order::Forward})==Result::DuplicateType);
    CHECK(graph.setChildren("CNL:Document",{"CNL:Stack"})==Result::Ok);
    CHECK(graph.setChildren("CNL:Path",{"CNL:Blur"})==Result::NotAContainer);
    uint64_t stack=0,a=0,b=0,reverse=0,c=0,d=0;
    CHECK(graph.add(Hierarchy::Root,"CNL:Stack","Main",stack)==Result::Ok);
    CHECK(graph.add(stack,"CNL:Path","A",a)==Result::Ok);
    CHECK(graph.add(stack,"CNL:Path","B",b)==Result::Ok);
    CHECK(graph.add(stack,"CNL:Reverse","R",reverse)==Result::Ok);
    CHECK(graph.add(reverse,"CNL:Path","C",c)==Result::Ok);
    CHECK(graph.add(reverse,"CNL:Path","D",d)==Result::Ok);
    uint64_t reject=9;
    CHECK(graph.add(reverse,"CNL:Blur","Bad",reject)==Result::DisallowedChild);
    CHECK(reject==0);
    CHECK(graph.add(stack,"CNL:NoSuchType","Bad",reject)==Result::UnknownType);
    CHECK(graph.reparent(stack,reverse,0)==Result::Cycle);
    CHECK(graph.reorder(stack,2)==Result::InvalidPosition);
    const auto trace=graph.evaluationTrace();
    const std::vector<std::string> expected={
     "begin:CNL:Document:ChapeLayer",
     "begin:CNL:Stack:Main",
     "emit:CNL:Path:A","emit:CNL:Path:B",
     "begin:CNL:Reverse:R","emit:CNL:Path:D","emit:CNL:Path:C",
     "end:CNL:Reverse:R","end:CNL:Stack:Main","end:CNL:Document:ChapeLayer"};
    CHECK(trace==expected);
    CHECK(graph.setChildren("CNL:Stack",{"CNL:Reverse"})==Result::DisallowedChild);
    CHECK(graph.canAdd(stack,"CNL:Path"));
    CHECK(graph.reorder(b,0)==Result::Ok);
    CHECK(graph.evaluationTrace()[2]=="emit:CNL:Path:B");
    CHECK(graph.evaluationTrace()[3]=="emit:CNL:Path:A");
    CHECK(graph.reparent(a,reverse,0)==Result::Ok);
    const auto moved=graph.evaluationTrace();
    // New reverse children [A,C,D] execute as D, C, A.
    CHECK(moved[3]=="begin:CNL:Reverse:R");
    CHECK(moved[4]=="emit:CNL:Path:D");
    CHECK(moved[5]=="emit:CNL:Path:C");
    CHECK(moved[6]=="emit:CNL:Path:A");
    CHECK(graph.get(a)->parent==reverse);
    CHECK(graph.nodeCount()==7); // root, group, two original paths, reverse, two nested
    // Parent-specific admission is a programmable rule, unlike a hard-coded class name.
    CHECK(graph.canAdd(Hierarchy::Root,"CNL:Stack"));
    CHECK(!graph.canAdd(Hierarchy::Root,"CNL:Path"));
    CHECK(!graph.canAdd(reverse,"CNL:Blur"));
    CHECK(graph.setOrder("CNL:Reverse",Order::Forward)==Result::Ok);
    auto altered=graph.evaluationTrace();
    CHECK(altered[4]=="emit:CNL:Path:A");
    CHECK(altered[5]=="emit:CNL:Path:C");
    CHECK(altered[6]=="emit:CNL:Path:D");
    std::cout<<"PASS ChapeLayer rules: plugin-owned child schemas, hierarchical reparent/cycle checks, forward/reverse evaluation semantics and stable IDs\n";
}
