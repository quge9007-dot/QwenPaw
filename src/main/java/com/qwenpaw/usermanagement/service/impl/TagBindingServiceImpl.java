package com.qwenpaw.usermanagement.service.impl;

import com.qwenpaw.usermanagement.dao.entity.TagBindingDO;
import com.qwenpaw.usermanagement.dao.mapper.TagBindingMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.constant.BindingConstants;
import com.qwenpaw.usermanagement.common.constant.TagConstants;
import com.qwenpaw.usermanagement.model.dto.TagBindingDTO;
import com.qwenpaw.usermanagement.model.request.BindTagRequest;
import com.qwenpaw.usermanagement.service.TagBindingService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * 标签绑定服务实现
 */
@Service
public class TagBindingServiceImpl implements TagBindingService {

    private final TagBindingMapper tagBindingMapper;
    private final com.qwenpaw.usermanagement.dao.mapper.TagMapper tagMapper;

    public TagBindingServiceImpl(TagBindingMapper tagBindingMapper, com.qwenpaw.usermanagement.dao.mapper.TagMapper tagMapper) {
        this.tagBindingMapper = tagBindingMapper;
        this.tagMapper = tagMapper;
    }

    @Override
    @Transactional
    public boolean bindTag(BindTagRequest request) {
        var tagDO = tagMapper.selectById(request.getTagId());
        if (tagDO == null) {
            throw new BizException(ErrorCode.TAG_NOT_FOUND);
        }

        var binding = tagBindingMapper.selectByUserIdAndTagId(request.getUserId(), request.getTagId());
        if (binding != null) {
            throw new BizException(ErrorCode.BINDING_ALREADY_EXISTS);
        }

        TagBindingDO tagBindingDO = new TagBindingDO();
        tagBindingDO.setUserId(request.getUserId());
        tagBindingDO.setTagId(request.getTagId());
        tagBindingDO.setSource(request.getSource() != null ? request.getSource() : BindingConstants.BINDING_SOURCE_MANUAL);
        tagBindingDO.setPkId(java.util.UUID.randomUUID().toString());
        tagBindingDO.setGmtCreate(LocalDateTime.now());
        tagBindingDO.setGmtModified(LocalDateTime.now());

        tagBindingMapper.insert(tagBindingDO);
        return true;
    }

    @Override
    @Transactional
    public boolean unbindTag(String userId, String tagId) {
        tagBindingMapper.deleteByUserIdAndTagId(userId, tagId);
        return true;
    }

    @Override
    public TagBindingDTO getBinding(String userId, String tagId) {
        var binding = tagBindingMapper.selectByUserIdAndTagId(userId, tagId);
        if (binding == null) {
            throw new BizException(ErrorCode.BINDING_NOT_FOUND);
        }
        return convertToDTO(binding);
    }

    private TagBindingDTO convertToDTO(TagBindingDO binding) {
        TagBindingDTO dto = new TagBindingDTO();
        dto.setUserId(binding.getUserId());
        dto.setTagId(binding.getTagId());
        dto.setSource(binding.getSource());
        dto.setGmtCreate(binding.getGmtCreate());
        return dto;
    }
}
