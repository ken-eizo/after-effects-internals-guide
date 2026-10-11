// CNL public-SDK-only, read-only project isolation gate.
// Shared by the safe AEGP preflight and any experimental native test.
// A pass does NOT prove complete isolation of AE global memory or user data.
#pragma once
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"

struct CNL_IsolationCheck {
 bool empty=false;
 const char* reason="not_run";
 A_long projects=-1;
 A_long non_root_items=-1;
 A_long render_queue_items=-1;
 A_Boolean dirty=TRUE;
 bool active_non_root=false;
};

inline CNL_IsolationCheck CNL_CheckDisposableProject(AEGP_SuiteHandler& suites){
 CNL_IsolationCheck s{};
 A_long count=0;
 if(suites.ProjSuite6()->AEGP_GetNumProjects(&count)!=A_Err_NONE){
  s.reason="project_count_unavailable";return s;
 }
 s.projects=count;
 if(count!=1){s.reason="project_count_not_one";return s;}
 AEGP_ProjectH project=nullptr;
 if(suites.ProjSuite6()->AEGP_GetProjectByIndex(0,&project)!=A_Err_NONE||!project){
  s.reason="project_handle_unavailable";return s;
 }
 if(suites.ProjSuite6()->AEGP_ProjectIsDirty(project,&s.dirty)!=A_Err_NONE){
  s.reason="project_dirty_state_unavailable";return s;
 }
 if(s.dirty){s.reason="project_dirty";return s;}
 AEGP_ItemH root=nullptr;
 if(suites.ProjSuite6()->AEGP_GetProjectRootFolder(project,&root)!=A_Err_NONE||!root){
  s.reason="project_root_unavailable";return s;
 }
 AEGP_ItemH active=nullptr;
 if(suites.ItemSuite9()->AEGP_GetActiveItem(&active)!=A_Err_NONE){
  s.reason="active_item_query_failed";return s;
 }
 s.active_non_root=active&&active!=root;
 if(s.active_non_root){s.reason="active_item_not_root";return s;}
 AEGP_ItemH item=nullptr;
 if(suites.ItemSuite9()->AEGP_GetFirstProjItem(project,&item)!=A_Err_NONE){
  s.reason="project_item_enumeration_failed";return s;
 }
 s.non_root_items=0;
 // Stop immediately on the first non-root item; enumeration does not
 // assume a complete count is cheap, and may include the root.
 unsigned traversed=0;
 while(item){
  if(item!=root){s.non_root_items=1;s.reason="non_root_project_item_found";return s;}
  AEGP_ItemH next=nullptr;
  if(suites.ItemSuite9()->AEGP_GetNextProjItem(project,item,&next)!=A_Err_NONE){
   s.reason="next_item_failed";return s;
  }
  if(next==item){s.reason="project_item_cycle";return s;}
  item=next;
  if(++traversed>1){s.reason="unexpected_multiple_root_items";return s;}
 }
 A_long rq=0;
 if(suites.RQItemSuite3()->AEGP_GetNumRQItems(&rq)!=A_Err_NONE){
  s.reason="render_queue_unavailable";return s;
 }
 s.render_queue_items=rq;
 if(rq!=0){s.reason="render_queue_not_empty";return s;}
 s.empty=true;s.reason="empty_project_preflight_only";
 return s;
}
