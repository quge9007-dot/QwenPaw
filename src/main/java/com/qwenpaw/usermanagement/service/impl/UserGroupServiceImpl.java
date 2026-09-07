package com.qwenpaw.usermanagement.service.impl;

import com.qwenpaw.usermanagement.dao.entity.UserGroupDO;
import com.qwenpaw.usermanagement.dao.mapper.UserGroupMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.model.dto.UserGroupDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserGroupRequest;
import com.qwenpaw.usermanagement.service.UserGroupService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 用户分群服务实现
 */
@Service
public class UserGroupServiceImpl implements UserGroupService {

    private final UserGroupMapper userGroupMapper;

    public UserGroupServiceImpl(UserGroupMapper userGroupMapper) {
        this.userGroupMapper = userGroupMapper;
    }

    @Override
    @Transactional
    public UserGroupDTO createGroup(CreateUserGroupRequest request) {
        UserGroupDO groupDO = new UserGroupDO();
        groupDO.setGroupId(java.util.UUID.randomUUID().toString());
        groupDO.setGroupName(request.getGroupName());
        groupDO.setGroupDesc(request.getGroupDesc());
        groupDO.setMatchType(request.getMatchType());
        groupDO.setStatus(1);
        groupDO.setPkId(java.util.UUID.randomUUID().toString());
        groupDO.setGmtCreate(LocalDateTime.now());
        groupDO.setGmtModified(LocalDateTime.now());

        userGroupMapper.insert(groupDO);
        return convertToDTO(groupDO);
    }

    @Override
    @Transactional
    public UserGroupDTO updateGroup(String groupId, CreateUserGroupRequest request) {
        UserGroupDO groupDO = userGroupMapper.selectById(groupId);
        if (groupDO == null) {
            throw new BizException(ErrorCode.GROUP_NOT_FOUND);
        }
        groupDO.setGroupName(request.getGroupName());
        groupDO.setGroupDesc(request.getGroupDesc());
        groupDO.setMatchType(request.getMatchType());
        groupDO.setGmtModified(LocalDateTime.now());
        userGroupMapper.updateById(groupDO);
        return convertToDTO(groupDO);
    }

    @Override
    @Transactional
    public boolean deleteGroup(String groupId) {
        UserGroupDO groupDO = userGroupMapper.selectById(groupId);
        if (groupDO == null) {
            throw new BizException(ErrorCode.GROUP_NOT_FOUND);
        }
        userGroupMapper.deleteById(groupId);
        return true;
    }

    @Override
    public UserGroupDTO getGroupById(String groupId) {
        UserGroupDO groupDO = userGroupMapper.selectById(groupId);
        if (groupDO == null) {
            throw new BizException(ErrorCode.GROUP_NOT_FOUND);
        }
        return convertToDTO(groupDO);
    }

    @Override
    public PageResult<UserGroupDTO> listGroups(int status, int page, int pageSize) {
        List<UserGroupDO> groupList = userGroupMapper.selectByStatus(status);
        List<UserGroupDTO> dtoList = groupList.stream().map(this::convertToDTO).collect(Collectors.toList());
        return new PageResult<>(dtoList.size(), page, pageSize, dtoList);
    }

    private UserGroupDTO convertToDTO(UserGroupDO groupDO) {
        UserGroupDTO dto = new UserGroupDTO();
        dto.setGroupId(groupDO.getGroupId());
        dto.setGroupName(groupDO.getGroupName());
        dto.setGroupDesc(groupDO.getGroupDesc());
        dto.setMatchType(groupDO.getMatchType());
        dto.setStatus(groupDO.getStatus());
        dto.setGmtCreate(groupDO.getGmtCreate());
        dto.setGmtModified(groupDO.getGmtModified());
        return dto;
    }
}
