package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.model.dto.TagDTO;
import com.qwenpaw.usermanagement.model.request.CreateTagRequest;
import com.qwenpaw.usermanagement.common.model.PageResult;

/**
 * 标签服务接口
 */
public interface TagService {

    TagDTO createTag(CreateTagRequest request);

    TagDTO updateTag(String tagId, CreateTagRequest request);

    boolean deleteTag(String tagId);

    TagDTO getTagById(String tagId);

    PageResult<TagDTO> listTags(String categoryId, int page, int pageSize);
}
