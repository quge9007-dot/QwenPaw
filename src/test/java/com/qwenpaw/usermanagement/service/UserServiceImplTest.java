package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.dao.entity.UserDO;
import com.qwenpaw.usermanagement.dao.mapper.UserMapper;
import com.qwenpaw.usermanagement.dao.mapper.TagBindingMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.model.dto.UserDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserRequest;
import com.qwenpaw.usermanagement.model.request.UpdateUserRequest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @Mock
    private UserMapper userMapper;

    @Mock
    private TagBindingMapper tagBindingMapper;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void should_createUser_when_validRequest() {
        CreateUserRequest request = new CreateUserRequest();
        request.setUserId("user001");
        request.setNickname("Test User");

        when(userMapper.selectById("user001")).thenReturn(null);
        when(userMapper.insert(any(UserDO.class))).thenReturn(1);

        UserDTO result = userService.createUser(request);

        assertThat(result).isNotNull();
        assertThat(result.getUserId()).isEqualTo("user001");
        assertThat(result.getNickname()).isEqualTo("Test User");
        assertThat(result.getStatus()).isEqualTo(1);
        verify(userMapper).insert(any(UserDO.class));
    }

    @Test
    void should_throwException_when_userAlreadyExists() {
        CreateUserRequest request = new CreateUserRequest();
        request.setUserId("user001");
        request.setNickname("Test User");

        when(userMapper.selectById("user001")).thenReturn(new UserDO());

        assertThatThrownBy(() -> userService.createUser(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.USER_ALREADY_EXISTS.getCode());
    }

    @Test
    void should_updateUser_when_validRequest() {
        UpdateUserRequest request = new UpdateUserRequest();
        request.setUserId("user001");
        request.setNickname("Updated User");

        UserDO existing = new UserDO();
        existing.setUserId("user001");
        existing.setNickname("Old User");
        when(userMapper.selectById("user001")).thenReturn(existing);
        when(userMapper.updateById(any(UserDO.class))).thenReturn(1);

        UserDTO result = userService.updateUser(request);

        assertThat(result).isNotNull();
        assertThat(result.getNickname()).isEqualTo("Updated User");
    }

    @Test
    void should_throwException_when_userNotFound() {
        UpdateUserRequest request = new UpdateUserRequest();
        request.setUserId("unknown");

        when(userMapper.selectById("unknown")).thenReturn(null);

        assertThatThrownBy(() -> userService.updateUser(request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.USER_NOT_FOUND.getCode());
    }

    @Test
    void should_deleteUser_when_exists() {
        UserDO existing = new UserDO();
        existing.setUserId("user001");
        when(userMapper.selectById("user001")).thenReturn(existing);
        when(userMapper.deleteById("user001")).thenReturn(1);

        boolean result = userService.deleteUser("user001");
        assertThat(result).isTrue();
    }

    @Test
    void should_getUserById_when_exists() {
        UserDO existing = new UserDO();
        existing.setUserId("user001");
        existing.setNickname("Test User");
        when(userMapper.selectById("user001")).thenReturn(existing);

        UserDTO result = userService.getUserById("user001");
        assertThat(result).isNotNull();
        assertThat(result.getUserId()).isEqualTo("user001");
    }

    @Test
    void should_listUsers_returnPageResult() {
        when(userMapper.countByStatus(null)).thenReturn(0L);
        PageResult<UserDTO> result = userService.listUsers(null, 1, 20);
        assertThat(result.getTotal()).isZero();
        assertThat(result.getList()).isEmpty();
    }
}
