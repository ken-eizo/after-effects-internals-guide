#pragma once
// Chape typed Timeline grammar: actual standalone native C++ runtime.
// Deliberately NOT an Adobe TDB/BEE object, native AE Layer or PF parameter.
#include <array>
#include <cstddef>
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace chape::timeline {
enum class Kind : uint8_t { Group=0, Float=1, Vector2=2, Color=3, Boolean=4 };
enum class Order : uint8_t { Forward=0, Reverse=1 };
enum class Interpolation : uint8_t { Hold=0, Linear=1 };
enum class Code : uint8_t {
 Ok=0, Missing, Invalid, UnknownType, Duplicate, Forbidden, WrongKind,
 Cycle, Range, Limit, Corrupt, EmptyHistory
};
struct Value {
 std::array<double,4> items{};
};
struct Key {
 int64_t tick=0;
 Value value{};
 Interpolation mode=Interpolation::Linear;
};
struct Type {
 std::string matchName;
 Kind kind=Kind::Group;
 std::vector<std::string> allowed;
 Order order=Order::Forward;
};
struct Node {
 uint64_t id=0,parent=0;
 std::string type,label;
 std::vector<uint64_t> children;
 Value base{};
 std::vector<Key> keys;
};
struct Event {
 uint64_t id;
 std::string kind;
 std::string matchName;
 Value value{};
};
class Document final {
public:
 static constexpr uint64_t Stage=1;
 static constexpr size_t MaxHistory=64;
 Document();
 Code registerType(Type type);
 Code permit(std::string parentType,std::vector<std::string> childTypes);
 Code setOrder(const std::string& type,Order order);
 Code add(uint64_t parent,const std::string& type,const std::string& label,uint64_t& id);
 Code move(uint64_t id,uint64_t newParent,size_t index);
 Code setBase(uint64_t id,Value value);
 Code setKey(uint64_t id,Key key);
 Code sample(uint64_t id,int64_t tick,Value& out) const;
 std::vector<Event> evaluate(int64_t tick) const;
 const Node* node(uint64_t id) const;
 const Type* type(const std::string& name) const;
 std::vector<uint8_t> archive() const;
 static Code restore(const std::vector<uint8_t>& data,Document& output);
 Code undo();
 Code redo();
 size_t undoDepth() const { return undo_.size(); }
 size_t redoDepth() const { return redo_.size(); }
private:
 struct State {
  std::map<std::string,Type> types;
  std::map<uint64_t,Node> nodes;
  uint64_t nextId=2;
 };
 State state_;
 std::vector<State> undo_,redo_;
 bool canAdd(uint64_t parent,const std::string& childType) const;
 bool descendant(uint64_t maybeAncestor,uint64_t candidate) const;
 bool validate(const State& state) const;
 void record(State&& old);
 Code setRawBase(uint64_t id,Value value);
 void visit(uint64_t id,int64_t tick,std::vector<Event>& out,size_t depth) const;
};
} // namespace chape::timeline
