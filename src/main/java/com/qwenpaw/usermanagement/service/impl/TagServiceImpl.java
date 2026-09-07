package com.qwenpaw.usermanagement.service.impl;

import com.qwenpaw.usermanagement.dao.entity.TagDO;
import com.qwenpaw.usermanagement.dao.mapper.TagMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.model.dto.TagDTO;
import com.qwenpaw.usermanagement.model.request.CreateTagRequest;
import com.qwenpaw.usermanagement.service.TagService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 标签服务实现
 */
@Service
public class TagServiceImpl implements TagService {

    private final TagMapper tagMapper;

    public TagServiceImpl(TagMapper tagMapper) {
        this.tagMapper = tagMapper;
    }

    @Override
    @Transactional
    public TagDTO createTag(CreateTagRequest request) {
        TagDO existing = tagMapper.selectById(request.getTagCode());
        if (existing != null) {
            throw new BizException(ErrorCode.TAG_ALREADY_EXISTS);
        }

        TagDO tagDO = new TagDO();
        tagDO.setTagId(request.getTagCode());
        tagDO.setTagName(request.getTagName());
        tagDO.setTagCode(request.getTagCode());
        tagDO.setCategoryId(request.getCategoryId());
        tagDO.setParentId(request.getParentId());
        tagDO.setTagLevel(request.getTagLevel() != null ? request.getTagLevel() : 1);
        tagDO.setStatus(1);
        tagDO.setSortOrder(request.getSortOrder() != null ? request.getSortOrder() : 0);
        tagDO.setPkId(java.util.UUID.randomUUID().toString());
        tagDO.setGmtCreate(LocalDateTime.now());
        tagDO.setGmtModified(LocalDateTime.now());

        tagMapper.insert(tagDO);
        return convertToDTO(tagDO);
    }

    @Override
    @Transactional
    public TagDTO updateTag(String tagId, CreateTagRequest request) {
        TagDO tagDO = tagMapper.selectById(tagId);
        if (tagDO == null) {
            throw new BizException(ErrorCode.TAG_NOT_FOUND);
        }

        tagDO.setTagName(request.getTagName());
        tagDO.setCategoryId(request.getCategoryId());
        tagDO.setParentId(request.getParentId());
        tagDO.setTagLevel(request.getTagLevel() != null ? request.getTagLevel() : 1);
        tagDO.setSortOrder(request.getSortOrder() != null ? request.getSortOrder() : 0);
        tagDO.setGmtModified(LocalDateTime.now());

        tagMapper.updateById(tagDO);
        return convertToDTO(tagDO);
    }

    @Override
    @Transactional
    public boolean deleteTag(String tagId) {
        TagDO tagDO = tagMapper.selectById(tagId);
        if (tagDO == null) {
            throw new BizException(ErrorCode.TAG_NOT_FOUND);
        }
        tagMapper.deleteById(tagId);
        return true;
    }

    @Override
    public TagDTO getTagById(String tagId) {
        TagDO tagDO = tagMapper.selectById(tagId);
        if (tagDO == null) {
            throw new BizException(ErrorCode.TAG_NOT_FOUND);
        }
        return convertToDTO(tagDO);
    }

    @Override
    public PageResult<TagDTO> listTags(String categoryId, int page, int pageSize) {
        List<TagDO> tagList;
        long total;
        if (categoryId != null) {
            total = tagMapper.countByCategoryId(categoryId);
            tagList = tagMapper.selectByCategoryId(categoryId);
        } else {
            total = tagMapper.selectAll().size();
            tagList = tagMapper.selectAll();
        }
        List<TagDTO> dtoList = tagList.stream().map(this::convertToDTO).collect(Collectors.toList());
        return new PageResult<>(total, page, pageSize, dtoList);
    }

    private TagDTO convertToDTO(TagDO tagDO) {
        TagDTO dto = new TagDTO();
        dto.setTagId(tagDO.getTagId());
        dto.setTagName(tagDO.getTagName());
        dto.setTagCode(tagDO.getTagCode());
        dto.setCategoryId(tagDO.getCategoryId());
        dto.setParentId(tagDO.getParentId());
        dto.setTagLevel(tagDO.getTagLevel());
        dto.setStatus(tagDO.getStatus());
        dto.setSortOrder(tagDO.getSortOrder());
        dto.setGmtCreate(tagDO.getGmtCreate());
        dto.setGmtModified(tagDO.getGmtModified());
        return dto;
    }
}
