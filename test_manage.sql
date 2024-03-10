/*
 Navicat Premium Data Transfer

 Source Server         : 本地
 Source Server Type    : MySQL
 Source Server Version : 50732
 Source Host           : localhost:3306
 Source Schema         : test_manage

 Target Server Type    : MySQL
 Target Server Version : 50732
 File Encoding         : 65001

 Date: 27/10/2021 10:20:23
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for bug
-- ----------------------------
DROP TABLE IF EXISTS `bug`;
CREATE TABLE `bug`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pro_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `version_id` int(11) NULL DEFAULT NULL,
  `demand_id` int(11) NULL DEFAULT NULL,
  `plan_id` int(11) NULL DEFAULT 0 COMMENT '发布性用例计划ID',
  `case_id` int(11) NULL DEFAULT NULL COMMENT '用例ID',
  `bug_num` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bug_level` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `report_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '报告人',
  `handle_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '处理人',
  `bug_state` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'bug状态',
  `isdelete` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of bug
-- ----------------------------
INSERT INTO `bug` VALUES (6, 'Azizi', 7, 8, 0, 31, 'bugly-10291', 'Hightest', '陈智斌', '张帅', 'progress', 1);
INSERT INTO `bug` VALUES (7, 'Azizi', 8, 3, 0, 16, '111', 'Medium', '冯思华', '罗帅', 'open', 0);
INSERT INTO `bug` VALUES (8, 'Azizi', 9, 4, 12, 26, '111', 'Medium', '冯思华', '罗帅', 'open', 0);

-- ----------------------------
-- Table structure for demand
-- ----------------------------
DROP TABLE IF EXISTS `demand`;
CREATE TABLE `demand`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pro_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `module_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `demand_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '需求名称',
  `tester` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '负责测试',
  `issuspend` int(11) NULL DEFAULT 0 COMMENT '0为正常  1为暂停',
  `plan_start` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '计划开始',
  `plan_end` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '计划结束',
  `reality_start` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '实际开始',
  `reality_end` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '实际结束',
  `version_id` int(11) NULL DEFAULT NULL COMMENT '版本ID',
  `jira_num` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'jira编号',
  `jira_state` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'jira状态',
  `remark` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '备注',
  `isdelete` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '需求表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of demand
-- ----------------------------
INSERT INTO `demand` VALUES (1, '77', 'live', '这是名称', '冯思华', 1, '2021-07-25', '2021-08-11', '10', '11', 1, 'BUYL123', '开发中', '这是备注', 1);
INSERT INTO `demand` VALUES (2, '77', 'user', '这是用例2', '冯思华', 1, '2021-07-25', '2021-08-11', '10', '11', 1, 'BUYL123', '开发中', '这是备注', 1);
INSERT INTO `demand` VALUES (3, 'Azizi', 'vip', '贵族红包', '冯思华', 0, '2021-10-11T16:00:00.000Z', '2021-10-25T16:00:00.000Z', '', '', 8, 'Buly123', '', '123456', 0);
INSERT INTO `demand` VALUES (4, 'Azizi', 'finance', '核心功能', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 9, '', '', '', 0);
INSERT INTO `demand` VALUES (5, 'Azizi', 'finance', 'P0用例', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 9, '', '', '', 0);
INSERT INTO `demand` VALUES (6, 'Azizi', 'vip', '平民红包', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-11-29T16:00:00.000Z', '', '', 8, '', '', '', 0);
INSERT INTO `demand` VALUES (7, 'Azizi', 'red', '会员红包', '陈智斌', 0, '2021-10-28T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 8, '', '', '', 0);
INSERT INTO `demand` VALUES (8, 'Azizi', 'lottery', '转盘规则', '陈智斌', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 7, '', '', '', 0);
INSERT INTO `demand` VALUES (9, 'xy', 'run', '周年庆玩法', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 14, '', '', '', 0);
INSERT INTO `demand` VALUES (10, 'xy', 'run', '会员制', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 14, '', '', '', 0);
INSERT INTO `demand` VALUES (11, 'xy', 'run', 'P0用例', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 13, '', '', '', 0);
INSERT INTO `demand` VALUES (12, 'xy', 'dating', '金融用例', '冯思华', 0, '2021-09-30T16:00:00.000Z', '2021-10-30T16:00:00.000Z', '', '', 13, '', '', '', 0);

-- ----------------------------
-- Table structure for release_plan
-- ----------------------------
DROP TABLE IF EXISTS `release_plan`;
CREATE TABLE `release_plan`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pro_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `plan_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '计划名称',
  `version_id` int(11) NULL DEFAULT NULL COMMENT '关联版本  0为日常回归',
  `plan_info` varchar(5000) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '计划内容',
  `create_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '创建者',
  `create_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `case_total` int(11) NULL DEFAULT NULL,
  `case_id_list` varchar(2000) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '用例列表',
  `demand_id_list` varchar(500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '版本列表',
  `remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `isdelete` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '发布性计划' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of release_plan
-- ----------------------------
INSERT INTO `release_plan` VALUES (12, 'Azizi', '红包活动2.0回归', 8, '[[5, 28], [5, 30], [4, 26], [4, 27]]', '冯思华', '2021-10-21 17:11:28', 4, '[28, 30, 26, 27]', '[4, 5]', '这是备注', 0);
INSERT INTO `release_plan` VALUES (13, 'Azizi', '日常回归', 0, '[[5, 28], [5, 30], [4, 26], [4, 27]]', '冯思华', '2021-10-26 10:14:07', 4, '[28, 30, 26, 27]', '[4, 5]', '这是备注哦', 0);
INSERT INTO `release_plan` VALUES (14, 'xy', '周年庆回归', 14, '[[12, 37], [12, 38], [11, 35], [11, 36]]', '冯思华', '2021-10-26 17:08:13', 4, '[37, 38, 35, 36]', '[11, 12]', '这是备注', 0);

-- ----------------------------
-- Table structure for review_case
-- ----------------------------
DROP TABLE IF EXISTS `review_case`;
CREATE TABLE `review_case`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pro_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `review_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '评审名称',
  `version_id` int(11) NULL DEFAULT NULL,
  `demand_id_list` varchar(5000) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '需求模块列表',
  `review_people` varchar(3000) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '审核人',
  `review_date` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '审核日期',
  `remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `isdelete` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of review_case
-- ----------------------------
INSERT INTO `review_case` VALUES (6, 'Azizi', '111', 8, '[6, 7, 3]', '陈智斌,冯思华', '2021-10-11T16:00:00.000Z', '111', 0);
INSERT INTO `review_case` VALUES (7, 'xy', '周年庆评审', 14, '[9, 10]', '罗帅,张帅,陈智斌,冯思华', '2021-10-26T16:00:00.000Z', '这是备注信息', 0);

-- ----------------------------
-- Table structure for run_plan
-- ----------------------------
DROP TABLE IF EXISTS `run_plan`;
CREATE TABLE `run_plan`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NULL DEFAULT NULL COMMENT '发布性计划ID',
  `case_id` int(11) NULL DEFAULT NULL COMMENT '用例ID',
  `run_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'PASS FAIL',
  `run_time` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '执行时间',
  `tester` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '执行人',
  `run_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 35 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '执行发布性用例记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of run_plan
-- ----------------------------
INSERT INTO `run_plan` VALUES (30, 12, 30, 'PASS', '2021-10-21', '冯思华', NULL);
INSERT INTO `run_plan` VALUES (31, 13, 26, 'PASS', '2021-10-26 12:12:39', '冯思华', '通过了');
INSERT INTO `run_plan` VALUES (32, 13, 28, 'PASS', '2021-10-26 12:12:39', '冯思华', '999');
INSERT INTO `run_plan` VALUES (33, 13, 30, 'FAIL', '2021-10-26 14:40:27', '冯思华', '123');
INSERT INTO `run_plan` VALUES (34, 14, 36, 'PASS', '2021-10-26 17:43:46', '冯思华', 'ok');

-- ----------------------------
-- Table structure for testcase
-- ----------------------------
DROP TABLE IF EXISTS `testcase`;
CREATE TABLE `testcase`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pro_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `case_name` varchar(150) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '用例名称',
  `case_type` int(11) NULL DEFAULT NULL COMMENT '1为版本用例   2为发布性用例',
  `version_id` int(11) NULL DEFAULT NULL COMMENT '版本ID',
  `demand_id` int(11) NULL DEFAULT NULL COMMENT '需求ID',
  `tag` varchar(150) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '标签',
  `case_level` varchar(11) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '用例级别',
  `tester` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '测试人员',
  `tester_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Fail Pass',
  `tester_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '执行时间',
  `tester_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `front_info` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '前置条件',
  `case_step` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '用例步骤',
  `case_result` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '预期结果',
  `review_state` int(11) NULL DEFAULT 0 COMMENT '评审状态  0为未评审   1为通过   2为不通过',
  `review_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '评审意见',
  `create_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '创建者',
  `android_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Android执行人',
  `android_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Android执行 PASS FAIL  BLOCK NOWORK',
  `android_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '安卓执行时间',
  `android_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ios_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'ios执行人',
  `ios_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'IOS执行结果 PASS FAIL  BLOCK NOWORK',
  `ios_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'IOS执行时间',
  `ios_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `manage_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '平台后台执行人',
  `manage_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '平台后台执行结果ID',
  `manage_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `manage_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `h5_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'h5执行人',
  `h5_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'h5执行结果 ',
  `h5_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `h5_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `applet_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '小程序执行人',
  `applet_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '小程序执行结果',
  `applet_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `applet_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `server_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '服务端执行人',
  `server_result` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '服务端执行结果ID',
  `server_runtime` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `server_remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `isrecovery` int(11) NULL DEFAULT 0 COMMENT '1为回收站',
  `recovery_people` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '回收站操作人',
  `isdelete` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 40 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '测试用例' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of testcase
-- ----------------------------
INSERT INTO `testcase` VALUES (16, 'Azizi', '更新后名称啊更新后名称啊更新后名称啊更新后名称啊更新后名称啊更新后名称啊更新后名称啊', 1, 8, 3, '', 'P0', '冯思华', 'PASS', '2021-10-24 21:29:20', '这是备注信息这是备注信息这是备注信息这是备注信息这是备注信息\n123', '<p>这是前置条件</p>', '<p>这是用例步骤</p>', '<p>这是预期结果</p>', 2, '123', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (18, 'Azizi', '会员红包用例', 1, 8, 6, '111', 'P0', '冯思华', 'PASS', '2021-10-26 14:15:24', '444', '<p>111</p>', '<p>222</p>', '<p>333</p>', 2, '123', '冯思华', '嘉明', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (19, 'Azizi', '平民红包', 1, 8, 7, '', 'P0', '陈智斌', '', '', '555', '<p>112</p>', '<p>333</p>', '<p>444</p>', 2, '1233', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (21, 'Azizi', '会员红包用例999', 1, 8, 6, '111', 'P0', '冯思华', 'PASS', '2021-10-26 14:32:28', '444', '<p>111</p>', '<p>222</p>', '<p>333</p>', 1, '不通过', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (26, 'Azizi', '日常回归用例', 2, 9, 4, '首页内容', 'P0', '冯思华', '', '', '这是备注', '<p>这是前置条件</p>', '<p>这是用例步骤</p>', '<p>这是预期结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (27, 'Azizi', '回归P0用例', 2, 9, 4, '核心功能', 'P0', '陈智斌', '', '', '这是备注', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是预期结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (28, 'Azizi', 'P0用例哦哦哦哦', 2, 9, 5, '', 'P0', '冯思华', '', '', '这是备注', '<p>这是前置条件</p>', '<p>这是用例步骤</p>', '<p>这是预期结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (29, 'Azizi', '转盘用例', 1, 7, 8, '', 'P0', '冯思华', 'FAIL', '2021-10-26 14:32:38', '备注', '<p>前置</p>', '<p>步骤</p>', '<p>结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (30, 'Azizi', '转盘用例', 2, 9, 5, '', 'P0', '冯思华', 'FAIL', '2021-10-21 20:28:56', '失败啦', '<p>前置</p>', '<p>步骤</p>', '<p>结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (31, 'Azizi', '111', 1, 7, 8, '这是转盘哦', 'P0', '冯思华', 'FAIL', '2021-10-22 17:03:17', '这是备注呢', '<p>111</p>', '<p>222</p>', '<p>333</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (32, 'Azizi', '拉拉', 1, 7, 8, '', 'P0', '冯思华', '', '', '44', '<p>1</p>', '<p>2</p>', '<p>3</p>', 0, '', '冯思华', '嘉明', 'PASS', '2021-10-24', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (33, 'xy', '核心玩法用例', 1, 14, 9, '', 'P0', '冯思华', 'PASS', '2021-10-22 17:03:17', '这是备注', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 1, 'no', '冯思华', '罗帅', '', '', '', '张帅', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (34, 'xy', '会员正常用例', 1, 14, 10, '', 'P1', '冯思华', 'FAIL', '2021-10-26 17:44:17', '这是备注', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 0, '', '冯思华', '罗帅', '', '', '', '张帅', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (35, 'xy', '核心玩法用例', 2, 13, 11, '', 'P0', '陈智斌', '', '', '', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (36, 'xy', '会员正常用例', 2, 13, 11, '', 'P1', '冯思华', '', '', '', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (37, 'xy', '核心玩法用例', 2, 13, 12, '', 'P0', '冯思华', '', '', '', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (38, 'xy', '会员正常用例', 2, 13, 12, '', 'P1', '冯思华', '', '', '', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 0, '', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);
INSERT INTO `testcase` VALUES (39, 'xy', '核心玩法用例2', 1, 14, 9, '', 'P0', '陈智斌', '', '', '这是备注', '<p>这是前置条件</p>', '<p>这是步骤</p>', '<p>这是结果</p>', 1, 'ok', '冯思华', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '', 0);

-- ----------------------------
-- Table structure for version
-- ----------------------------
DROP TABLE IF EXISTS `version`;
CREATE TABLE `version`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pro_code` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `version_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '版本名称',
  `dingding_conf` varchar(500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '钉钉配置',
  `remark` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '备注',
  `isrelease` int(11) NULL DEFAULT 0 COMMENT '0为版本   1为发布性',
  `isdelete` int(11) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '版本表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of version
-- ----------------------------
INSERT INTO `version` VALUES (1, '77', '1.0版本', '111', '223', 0, 1);
INSERT INTO `version` VALUES (2, '77', '1.1版本', '22', '33', 0, 1);
INSERT INTO `version` VALUES (3, '77', '发布性用例', NULL, NULL, 1, 0);
INSERT INTO `version` VALUES (4, '77', '77版本配置', '这是钉钉配置', '这是备足', 0, 1);
INSERT INTO `version` VALUES (5, '77', '哈哈', '拉拉', '兔兔', 0, 1);
INSERT INTO `version` VALUES (6, '77', '114', '223', '336', 0, 1);
INSERT INTO `version` VALUES (7, 'Azizi', '转盘活动1.0', '', '', 0, 0);
INSERT INTO `version` VALUES (8, 'Azizi', '红包活动2.0', '', '', 0, 0);
INSERT INTO `version` VALUES (9, 'Azizi', '发布性用例', NULL, NULL, 1, 0);
INSERT INTO `version` VALUES (10, '77', '红包版本', '', '', 0, 0);
INSERT INTO `version` VALUES (12, 'my', '发布性用例', '', '', 1, 0);
INSERT INTO `version` VALUES (13, 'xy', '发布性用例', '', '', 1, 0);
INSERT INTO `version` VALUES (14, 'xy', '周年庆活动', '', '', 0, 0);

SET FOREIGN_KEY_CHECKS = 1;
