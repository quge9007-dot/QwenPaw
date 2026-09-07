package com.qwenpaw.usermanagement.service.impl;

import com.qwenpaw.usermanagement.dao.entity.UserDO;
import com.qwenpaw.usermanagement.dao.mapper.UserMapper;
import com.qwenpaw.usermanagement.dao.mapper.TagBindingMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.constant.UserConstants;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.model.dto.UserDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserRequest;
import com.qwenpaw.usermanagement.model.request.UpdateUserRequest;
import com.qwenpaw.usermanagement.service.UserService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 用户服务实现
 */
@Service
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final TagBindingMapper tagBindingMapper;

    public UserServiceImpl(UserMapper userMapper, TagBindingMapper tagBindingMapper) {
        this.userMapper = userMapper;
        this.tagBindingMapper = tagBindingMapper;
    }

    @Override
    @Transactional
    public UserDTO createUser(CreateUserRequest request) {
        UserDO existing = userMapper.selectById(request.getUserId());
        if (existing != null) {
            throw new BizException(ErrorCode.USER_ALREADY_EXISTS);
        }

        UserDO userDO = new UserDO();
        userDO.setUserId(request.getUserId());
        userDO.setNickname(request.getNickname());
        userDO.setAvatarUrl(request.getAvatarUrl());
        userDO.setStatus(UserConstants.USER_STATUS_NORMAL);
        userDO.setTagCount(0);
        userDO.setPkId(java.util.UUID.randomUUID().toString());
        userDO.setGmtCreate(LocalDateTime.now());
        userDO.setGmtModified(LocalDateTime.now());

        userMapper.insert(userDO);
        return convertToDTO(userDO);
    }

    @Override
    @Transactional
    public UserDTO updateUser(UpdateUserRequest request) {
        UserDO userDO = userMapper.selectById(request.getUserId());
        if (userDO == null) {
            throw new BizException(ErrorCode.USER_NOT_FOUND);
        }

        if (request.getNickname() != null) {
            userDO.setNickname(request.getNickname());
        }
        if (request.getAvatarUrl() != null) {
            userDO.setAvatarUrl(request.getAvatarUrl());
        }
        if (request.getStatus() != null) {
            userDO.setStatus(request.getStatus());
        }
        userDO.setGmtModified(LocalDateTime.now());

        userMapper.updateById(userDO);
        return convertToDTO(userDO);
    }

    @Override
    @Transactional
    public boolean deleteUser(String userId) {
        UserDO userDO = userMapper.selectById(userId);
        if (userDO == null) {
            throw new BizException(ErrorCode.USER_NOT_FOUND);
        }
        userMapper.deleteById(userId);
        return true;
    }

    @Override
    public UserDTO getUserById(String userId) {
        UserDO userDO = userMapper.selectById(userId);
        if (userDO == null) {
            throw new BizException(ErrorCode.USER_NOT_FOUND);
        }
        return convertToDTO(userDO);
    }

    @Override
    public PageResult<UserDTO> listUsers(Integer status, int page, int pageSize) {
        long total = userMapper.countByStatus(status);
        if (total == 0) {
            return PageResult.empty();
        }
        List<UserDO> userList = userMapper.selectByStatus(status);
        List<UserDTO> dtoList = userList.stream().map(this::convertToDTO).collect(Collectors.toList());
        return new PageResult<>(total, page, pageSize, dtoList);
    }

    @Override
    @Transactional
    public boolean bindTag(String userId, String tagId) {
        UserDO userDO = userMapper.selectById(userId);
        if (userDO == null) {
            throw new BizException(ErrorCode.USER_NOT_FOUND);
        }
        var binding = tagBindingMapper.selectByUserIdAndTagId(userId, tagId);
        if (binding != null) {
            throw new BizException(ErrorCode.BINDING_ALREADY_EXISTS);
        }
        // binding logic handled by TagService for tag existence check
        return true;
    }

    @Override
    @Transactional
    public boolean unbindTag(String userId, String tagId) {
        tagBindingMapper.deleteByUserIdAndTagId(userId, tagId);
        return true;
    }

    private UserDTO convertToDTO(UserDO userDO) {
        UserDTO dto = new UserDTO();
        dto.setUserId(userDO.getUserId());
        dto.setNickname(userDO.getNickname());
        dto.setAvatarUrl(userDO.getAvatarUrl());
        dto.setStatus(userDO.getStatus());
        dto.setTagCount(userDO.getTagCount());
        dto.setGmtCreate(userDO.getGmtCreate());
        dto.setGmtModified(userDO.getGmtModified());
        return dto;
    }
}
