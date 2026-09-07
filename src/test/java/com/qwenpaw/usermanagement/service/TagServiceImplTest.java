package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.dao.entity.TagDO;
import com.qwenpaw.usermanagement.dao.mapper.TagMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.model.dto.TagDTO;
import com.qwenpaw.usermanagement.model.request.CreateTagRequest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TagServiceImplTest {

    @Mock
    private TagMapper tagMapper;

    @InjectMocks
    private TagServiceImpl tagService;

    @Test
    void should_createTag_when_validRequest() {
        CreateTagRequest request = new CreateTagRequest();
        request.setTagName("VIP");
        request.setTagCode("TAG_VIP");
        request.setCategoryId("cat001");

        when(tagMapper.selectById("TAG_VIP")).thenReturn(null);
        when(tagMapper.insert(any(TagDO.class))).thenReturn(1);

        TagDTO result = tagService.createTag(request);

        assertThat(result).isNotNull();
        assertThat(result.getTagName()).isEqualTo("VIP");
        assertThat(result.getTagCode()).isEqualTo("TAG_VIP");
        verify(tagMapper).insert(any(TagDO.class));
    }

    @Test
    void should_throwException_when_tagAlreadyExists() {
        CreateTagRequest request = new CreateTagRequest();
        request.setTagName("VIP");
        request.setTagCode("TAG_VIP");

        when(tagMapper.selectById("TAG_VIP")).thenReturn(new TagDO());

        assertThatThrownBy(() -> tagService.createTag(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.TAG_ALREADY_EXISTS.getCode());
    }

    @Test
    void should_getTagById_when_exists() {
        TagDO existing = new TagDO();
        existing.setTagId("tag001");
        existing.setTagName("VIP");
        when(tagMapper.selectById("tag001")).thenReturn(existing);

        TagDTO result = tagService.getTagById("tag001");
        assertThat(result).isNotNull();
        assertThat(result.getTagName()).isEqualTo("VIP");
    }

    @Test
    void should_throwException_when_tagNotFound() {
        when(tagMapper.selectById("unknown")).thenReturn(null);

        assertThatThrownBy(() -> tagService.getTagById("unknown"))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.TAG_NOT_FOUND.getCode());
    }

    @Test
    void should_listTags_returnPageResult() {
        TagDO tag = new TagDO();
        tag.setTagId("tag001");
        when(tagMapper.selectAll()).thenReturn(List.of(tag));
        when(tagMapper.countByCategoryId(null)).thenReturn(0L);

        PageResult<TagDTO> result = tagService.listTags(null, 1, 20);
        assertThat(result.getTotal()).isZero();
    }

    @Test
    void should_updateTag_when_exists() {
        TagDO existing = new TagDO();
        existing.setTagId("tag001");
        existing.setTagName("Old");
        when(tagMapper.selectById("tag001")).thenReturn(existing);
        when(tagMapper.updateById(any(TagDO.class))).thenReturn(1);

        CreateTagRequest request = new CreateTagRequest();
        request.setTagName("Updated");
        request.setTagCode("tag001");
        request.setCategoryId("cat001");

        TagDTO result = tagService.updateTag("tag001", request);
        assertThat(result.getTagName()).isEqualTo("Updated");
    }
}
