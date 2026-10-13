#pragma once
// ChapeLayer-owned, explicitly configurable hierarchical node schema.
// This is a CNL native C++ reference evaluator; it does not register BEE/TDB.
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace chape {
enum class Order : uint8_t { Forward = 0, Reverse = 1 };
enum class Result : uint8_t {
    Ok = 0, UnknownType, InvalidParent, DisallowedChild,
    DuplicateType, Cycle, InvalidPosition, NotAContainer, Limit
};
struct Type {
    std::string matchName;
    std::vector<std::string> permittedChildren;
    bool container = false;
    Order evaluationOrder = Order::Forward;
};
struct Node {
    uint64_t id = 0;
    uint64_t parent = 0;
    std::string type;
    std::string label;
    std::vector<uint64_t> children;
};
class Hierarchy final {
public:
    static constexpr uint64_t Root = 1;
    Hierarchy();
    Result registerType(Type type);
    Result setChildren(const std::string& parentType,std::vector<std::string> allowed);
    Result setOrder(const std::string& type,Order order);
    Result add(uint64_t parent, const std::string& type, std::string label, uint64_t& newId);
    Result reorder(uint64_t nodeId, size_t targetIndex);
    Result reparent(uint64_t nodeId, uint64_t newParent, size_t targetIndex);
    bool canAdd(uint64_t parent, const std::string& type) const;
    const Node* get(uint64_t id) const;
    std::vector<std::string> evaluationTrace() const;
    size_t nodeCount() const {return nodes_.size();}
private:
    bool isAncestor(uint64_t possibleAncestor, uint64_t nodeId) const;
    void evaluate(uint64_t id, std::vector<std::string>& trace, unsigned depth) const;
    std::unordered_map<std::string,Type> types_;
    std::unordered_map<uint64_t,Node> nodes_;
    uint64_t nextId_ = Root+1;
};
}
