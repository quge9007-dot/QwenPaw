package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.model.dto.UserGroupDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserGroupRequest;
import com.qwenpaw.usermanagement.common.model.PageResult;

/**
 * 用户分群服务接口
 */
public interface UserGroupService {

    UserGroupDTO createGroup(CreateUserGroupRequest request);

    UserGroupDTO updateGroup(String groupId, CreateUserGroupRequest request);

    boolean deleteGroup(String groupId);

    UserGroupDTO getGroupById(String groupId);

    PageResult<UserGroupDTO> listGroups(int status, int page, int pageSize);
}
