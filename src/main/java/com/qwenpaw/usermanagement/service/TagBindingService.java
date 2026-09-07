package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.model.dto.TagBindingDTO;
import com.qwenpaw.usermanagement.model.request.BindTagRequest;

/**
 * 标签绑定服务接口
 */
public interface TagBindingService {

    boolean bindTag(BindTagRequest request);

    boolean unbindTag(String userId, String tagId);

    TagBindingDTO getBinding(String userId, String tagId);
}
