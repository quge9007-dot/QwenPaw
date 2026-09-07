package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.model.dto.MatchResultDTO;
import com.qwenpaw.usermanagement.model.dto.UserDTO;
import com.qwenpaw.usermanagement.model.request.TagMatchRequest;

/**
 * 标签匹配服务接口
 */
public interface TagMatchService {

    MatchResultDTO matchUsersByTags(TagMatchRequest request);
}
