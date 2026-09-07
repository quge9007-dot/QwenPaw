package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.dao.entity.UserBehaviorDO;
import com.qwenpaw.usermanagement.dao.mapper.UserBehaviorMapper;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 用户行为控制器
 */
@RestController
@RequestMapping("/api/v1/behaviors")
public class UserBehaviorController {

    private final UserBehaviorMapper userBehaviorMapper;

    public UserBehaviorController(UserBehaviorMapper userBehaviorMapper) {
        this.userBehaviorMapper = userBehaviorMapper;
    }

    @PostMapping
    public UserBehaviorDO createBehavior(@RequestBody UserBehaviorDO behavior) {
        userBehaviorMapper.insert(behavior);
        return behavior;
    }

    @GetMapping("/{userId}")
    public List<UserBehaviorDO> getBehaviors(@PathVariable String userId) {
        return userBehaviorMapper.selectByUserId(userId);
    }
}
