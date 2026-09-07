package com.qwenpaw.usermanagement.service.impl;

import com.qwenpaw.usermanagement.common.constant.TagConstants;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.dao.entity.UserDO;
import com.qwenpaw.usermanagement.dao.mapper.UserMapper;
import com.qwenpaw.usermanagement.model.dto.MatchResultDTO;
import com.qwenpaw.usermanagement.model.dto.UserDTO;
import com.qwenpaw.usermanagement.model.request.TagMatchRequest;
import com.qwenpaw.usermanagement.service.TagMatchService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 标签匹配服务实现
 */
@Service
public class TagMatchServiceImpl implements TagMatchService {

    private final UserMapper userMapper;

    public TagMatchServiceImpl(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @Override
    public MatchResultDTO matchUsersByTags(TagMatchRequest request) {
        if (request.getTagIds() == null || request.getTagIds().isEmpty()) {
            throw new BizException(ErrorCode.MATCH_PARAM_INVALID);
        }

        List<UserDO> userList;
        if (request.getMatchType() != null && request.getMatchType() == TagConstants.MATCH_TYPE_ALL) {
            userList = userMapper.selectByTagIds(request.getTagIds());
        } else {
            userList = userMapper.selectByTagIds(request.getTagIds());
        }

        List<UserDTO> dtoList = userList.stream().map(this::convertToDTO).collect(Collectors.toList());
        return new MatchResultDTO(userList.size(), dtoList,
            request.getMatchType() != null && request.getMatchType() == TagConstants.MATCH_TYPE_ALL ? "ALL" : "ANY");
    }

    private UserDTO convertToDTO(UserDO userDO) {
        UserDTO dto = new UserDTO();
        dto.setUserId(userDO.getUserId());
        dto.setNickname(userDO.getNickname());
        dto.setAvatarUrl(userDO.getAvatarUrl());
        dto.setStatus(userDO.getStatus());
        dto.setTagCount(userDO.getTagCount());
        return dto;
    }
}
