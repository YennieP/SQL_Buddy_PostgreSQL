# Mentor模块整合计划

## 📋 整合优先级

### Priority 1: 核心功能页面（必须今天完成）

- [ ] **mentor_dashboard.html**
  - 描述: 导师主页 - 显示统计和待审核列表
  - 状态: ✅ 需要整合

- [ ] **create_problem.html**
  - 描述: 创建问题 - Mentor的核心功能
  - 状态: ✅ 需要整合

- [ ] **review_attempts.html**
  - 描述: 审核学生提交 - 重要功能
  - 状态: ✅ 需要整合


### Priority 2: 问题管理页面（明天完成）

- [ ] **my_problems.html**
  - 描述: 我创建的问题列表
  - 状态: ✅ 需要整合

- [ ] **edit_problem.html**
  - 描述: 编辑问题
  - 状态: ✅ 需要整合

- [ ] **problem_analytics.html**
  - 描述: 问题分析统计
  - 状态: ✅ 需要整合


### Priority 3: 资源管理和高级功能（可选）

- [ ] **upload_resource.html**
  - 描述: 上传学习资源
  - 状态: ✅ 需要整合

- [ ] **my_resources.html**
  - 描述: 我的资源列表
  - 状态: ✅ 需要整合

- [ ] **resource_analytics.html**
  - 描述: 资源统计
  - 状态: ✅ 需要整合

- [ ] **mentor_nl_query.html**
  - 描述: 自然语言查询
  - 状态: ✅ 需要整合


---

## 🔧 后端View函数清单

发现的Mentor view函数：
1. `_get_current_mentor()`
2. `mentor_dashboard()`
3. `create_problem()`
4. `my_problems()`
5. `problem_analytics()`
6. `review_attempts()`
7. `add_feedback()`
8. `upload_resource()`
9. `my_resources()`
10. `resource_analytics()`
11. `mentor_nl_query()`
12. `edit_problem()`
13. `delete_problem()`

---

## 📝 整合标准流程

每个页面：
1. 备份旧模板
2. 从新UI复制或创建
3. 调整变量名匹配后端
4. 测试所有功能
5. 确认无误后打勾

---

## 🎯 今天目标

完成Priority 1的3个核心页面
