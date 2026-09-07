package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.dao.entity.TagBindingDO;
import com.qwenpaw.usermanagement.dao.entity.TagDO;
import com.qwenpaw.usermanagement.dao.mapper.TagBindingMapper;
import com.qwenpaw.usermanagement.dao.mapper.TagMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.model.dto.TagBindingDTO;
import com.qwenpaw.usermanagement.model.request.BindTagRequest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TagBindingServiceImplTest {

    @Mock
    private TagBindingMapper tagBindingMapper;

    @Mock
    private TagMapper tagMapper;

    @InjectMocks
    private TagBindingServiceImpl tagBindingService;

    @Test
    void should_bindTag_when_validRequest() {
        TagDO tagDO = new TagDO();
        tagDO.setTagId("tag001");
        when(tagMapper.selectById("tag001")).thenReturn(tagDO);
        when(tagBindingMapper.selectByUserIdAndTagId("user001", "tag001")).thenReturn(null);
        when(tagBindingMapper.insert(any(TagBindingDO.class))).thenReturn(1);

        BindTagRequest request = new BindTagRequest();
        request.setUserId("user001");
        request.setTagId("tag001");
        request.setSource(1);

        boolean result = tagBindingService.bindTag(request);
        assertThat(result).isTrue();
        verify(tagBindingMapper).insert(any(TagBindingDO.class));
    }

    @Test
    void should_throwException_when_bindingAlreadyExists() {
        TagDO tagDO = new TagDO();
        tagDO.setTagId("tag001");
        when(tagMapper.selectById("tag001")).thenReturn(tagDO);
        when(tagBindingMapper.selectByUserIdAndTagId("user001", "tag001")).thenReturn(new TagBindingDO());

        BindTagRequest request = new BindTagRequest();
        request.setUserId("user001");
        request.setTagId("tag001");

        assertThatThrownBy(() -> tagBindingService.bindTag(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.BINDING_ALREADY_EXISTS.getCode());
    }

    @Test
    void should_throwException_when_tagNotFound() {
        when(tagMapper.selectById("tag001")).thenReturn(null);

        BindTagRequest request = new BindTagRequest();
        request.setUserId("user001");
        request.setTagId("tag001");

        assertThatThrownBy(() -> tagBindingService.bindTag(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.TAG_NOT_FOUND.getCode());
    }

    @Test
    void should_unbindTag_when_exists() {
        when(tagBindingMapper.selectByUserIdAndTagId("user001", "tag001")).thenReturn(new TagBindingDO());
        when(tagBindingMapper.deleteByUserIdAndTagId("user001", "tag001")).thenReturn(1);

        boolean result = tagBindingService.unbindTag("user001", "tag001");
        assertThat(result).isTrue();
    }
}
