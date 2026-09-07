package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.dao.entity.UserAttributeDO;
import com.qwenpaw.usermanagement.dao.mapper.UserAttributeMapper;
import org.springframework.web.bind.annotation.*;

/**
 * 用户属性控制器
 */
@RestController
@RequestMapping("/api/v1/attributes")
public class UserAttributeController {

    private final UserAttributeMapper userAttributeMapper;

    public UserAttributeController(UserAttributeMapper userAttributeMapper) {
        this.userAttributeMapper = userAttributeMapper;
    }

    @PostMapping
    public UserAttributeDO createAttribute(@RequestBody UserAttributeDO attribute) {
        userAttributeMapper.insert(attribute);
        return attribute;
    }

    @GetMapping("/{userId}")
    public UserAttributeDO getAttribute(@PathVariable String userId, @RequestParam String attrKey) {
        return userAttributeMapper.selectByUserIdAndKey(userId, attrKey);
    }
}
