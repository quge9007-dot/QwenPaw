package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.model.dto.UserDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserRequest;
import com.qwenpaw.usermanagement.model.request.UpdateUserRequest;
import com.qwenpaw.usermanagement.common.model.PageResult;

/**
 * 用户服务接口
 */
public interface UserService {

    UserDTO createUser(CreateUserRequest request);

    UserDTO updateUser(UpdateUserRequest request);

    boolean deleteUser(String userId);

    UserDTO getUserById(String userId);

    PageResult<UserDTO> listUsers(Integer status, int page, int pageSize);

    boolean bindTag(String userId, String tagId);

    boolean unbindTag(String userId, String tagId);
}
