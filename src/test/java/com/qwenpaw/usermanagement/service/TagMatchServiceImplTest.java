package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.dao.entity.UserDO;
import com.qwenpaw.usermanagement.dao.mapper.UserMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.model.dto.MatchResultDTO;
import com.qwenpaw.usermanagement.model.request.TagMatchRequest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TagMatchServiceImplTest {

    @Mock
    private UserMapper userMapper;

    @InjectMocks
    private TagMatchServiceImpl tagMatchService;

    @Test
    void should_matchUsers_when_allMatchType() {
        UserDO user = new UserDO();
        user.setUserId("user001");
        user.setNickname("Test User");
        when(userMapper.selectByTagIds(List.of("tag001"))).thenReturn(List.of(user));

        TagMatchRequest request = new TagMatchRequest();
        request.setTagIds(List.of("tag001"));
        request.setMatchType(1);

        MatchResultDTO result = tagMatchService.matchUsersByTags(request);

        assertThat(result).isNotNull();
        assertThat(result.getTotal()).isOne();
        assertThat(result.getUserList()).hasSize(1);
        assertThat(result.getMatchType()).isEqualTo("ALL");
    }

    @Test
    void should_matchUsers_when_anyMatchType() {
        UserDO user = new UserDO();
        user.setUserId("user001");
        when(userMapper.selectByTagIds(List.of("tag001"))).thenReturn(List.of(user));

        TagMatchRequest request = new TagMatchRequest();
        request.setTagIds(List.of("tag001"));
        request.setMatchType(0);

        MatchResultDTO result = tagMatchService.matchUsersByTags(request);

        assertThat(result).isNotNull();
        assertThat(result.getTotal()).isOne();
    }

    @Test
    void should_throwException_when_tagIdsEmpty() {
        TagMatchRequest request = new TagMatchRequest();
        request.setTagIds(List.of());

        assertThatThrownBy(() -> tagMatchService.matchUsersByTags(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.MATCH_PARAM_INVALID.getCode());
    }

    @Test
    void should_throwException_when_tagIdsNull() {
        TagMatchRequest request = new TagMatchRequest();

        assertThatThrownBy(() -> tagMatchService.matchUsersByTags(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.MATCH_PARAM_INVALID.getCode());
    }
}
