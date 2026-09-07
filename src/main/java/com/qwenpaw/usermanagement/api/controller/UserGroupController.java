package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.model.dto.UserGroupDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserGroupRequest;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.service.UserGroupService;
import org.springframework.web.bind.annotation.*;

/**
 * 用户分群管理控制器
 */
@RestController
@RequestMapping("/api/v1/groups")
public class UserGroupController {

    private final UserGroupService userGroupService;

    public UserGroupController(UserGroupService userGroupService) {
        this.userGroupService = userGroupService;
    }

    @PostMapping
    public UserGroupDTO createGroup(@RequestBody CreateUserGroupRequest request) {
        return userGroupService.createGroup(request);
    }

    @PutMapping("/{groupId}")
    public UserGroupDTO updateGroup(@PathVariable String groupId, @RequestBody CreateUserGroupRequest request) {
        return userGroupService.updateGroup(groupId, request);
    }

    @DeleteMapping("/{groupId}")
    public boolean deleteGroup(@PathVariable String groupId) {
        return userGroupService.deleteGroup(groupId);
    }

    @GetMapping("/{groupId}")
    public UserGroupDTO getGroupById(@PathVariable String groupId) {
        return userGroupService.getGroupById(groupId);
    }

    @GetMapping
    public PageResult<UserGroupDTO> listGroups(
            @RequestParam(required = false) Integer status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize) {
        return userGroupService.listGroups(status, page, pageSize);
    }
}
