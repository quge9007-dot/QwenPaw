package com.qwenpaw.usermanagement.service;

import com.qwenpaw.usermanagement.dao.entity.UserGroupDO;
import com.qwenpaw.usermanagement.dao.mapper.UserGroupMapper;
import com.qwenpaw.usermanagement.common.exception.BizException;
import com.qwenpaw.usermanagement.common.exception.ErrorCode;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.model.dto.UserGroupDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserGroupRequest;
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
class UserGroupServiceImplTest {

    @Mock
    private UserGroupMapper userGroupMapper;

    @InjectMocks
    private UserGroupServiceImpl userGroupService;

    @Test
    void should_createGroup_when_validRequest() {
        CreateUserGroupRequest request = new CreateUserGroupRequest();
        request.setGroupName("VIP Group");
        request.setMatchType(1);

        when(userGroupMapper.insert(any(UserGroupDO.class))).thenReturn(1);

        UserGroupDTO result = userGroupService.createGroup(request);

        assertThat(result).isNotNull();
        assertThat(result.getGroupName()).isEqualTo("VIP Group");
        assertThat(result.getMatchType()).isEqualTo(1);
    }

    @Test
    void should_throwException_when_groupNotFound() {
        when(userGroupMapper.selectById("unknown")).thenReturn(null);

        CreateUserGroupRequest request = new CreateUserGroupRequest();
        request.setGroupName("Test");
        request.setMatchType(1);

        assertThatThrownBy(() -> userGroupService.updateGroup("unknown", request))
            .isInstanceOf(BizException.class)
            .hasFieldOrPropertyWithValue("code", ErrorCode.GROUP_NOT_FOUND.getCode());
    }

    @Test
    void should_getGroupById_when_exists() {
        UserGroupDO group = new UserGroupDO();
        group.setGroupId("grp001");
        group.setGroupName("VIP Group");
        when(userGroupMapper.selectById("grp001")).thenReturn(group);

        UserGroupDTO result = userGroupService.getGroupById("grp001");
        assertThat(result).isNotNull();
        assertThat(result.getGroupName()).isEqualTo("VIP Group");
    }

    @Test
    void should_deleteGroup_when_exists() {
        UserGroupDO group = new UserGroupDO();
        group.setGroupId("grp001");
        when(userGroupMapper.selectById("grp001")).thenReturn(group);
        when(userGroupMapper.deleteById("grp001")).thenReturn(1);

        boolean result = userGroupService.deleteGroup("grp001");
        assertThat(result).isTrue();
    }

    @Test
    void should_listGroups_returnPageResult() {
        UserGroupDO group = new UserGroupDO();
        group.setGroupId("grp001");
        when(userGroupMapper.selectByStatus(1)).thenReturn(List.of(group));

        PageResult<UserGroupDTO> result = userGroupService.listGroups(1, 1, 20);
        assertThat(result.getTotal()).isOne();
        assertThat(result.getList()).hasSize(1);
    }
}
