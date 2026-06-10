-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 10, 2026 at 11:16 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `doc_verify_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `candidates`
--

CREATE TABLE `candidates` (
  `id` int(11) NOT NULL,
  `full_name` varchar(200) NOT NULL,
  `email` varchar(150) DEFAULT NULL,
  `position_applied` varchar(150) DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `candidates`
--

INSERT INTO `candidates` (`id`, `full_name`, `email`, `position_applied`, `created_by`, `created_at`) VALUES
(11, 'UWAMAHORO SANDRINE', 'sandrine@gmail.com', 'IT', 1, '2026-05-16 20:13:27'),
(17, 'MBABAZI Diane', 'dianne@gmail.com', 'IT', 1, '2026-05-24 13:13:26'),
(18, 'IZIBIDUKWIYE Kevin', '', '', 1, '2026-05-24 13:20:15'),
(20, 'IMANISHIMWE Nadine', '', '', 1, '2026-05-24 23:01:03'),
(22, 'IRADUKUNDA Lambert', '', '', 1, '2026-06-02 14:15:44'),
(24, 'Rene', '', '', 1, '2026-06-03 10:07:30'),
(25, 'janviel', '', '', 1, '2026-06-03 20:50:30'),
(26, 'UWIRINGIYIMANA Elie', '', '', 1, '2026-06-06 08:16:57'),
(27, 'ERIC', '', '', 1, '2026-06-06 09:19:58'),
(28, 'JACKY', '', '', 1, '2026-06-06 09:29:44'),
(30, 'TUMWINE Eric', '', '', 1, '2026-06-08 22:10:32'),
(31, 'MUKESHIMANA Delphine', '', '', 1, '2026-06-08 22:14:18'),
(32, 'TUMWINE', '', '', 1, '2026-06-08 22:23:45'),
(33, 'NZAYISENGA Emmanuel', '', '', 1, '2026-06-08 22:27:41'),
(34, 'HASHIMWE Janvier', '', '', 1, '2026-06-09 22:10:58'),
(35, 'NIYIGENA Sarah', '', '', 1, '2026-06-09 23:07:11'),
(36, 'SIMBA ALOYS', '', '', 1, '2026-06-10 08:01:23');

-- --------------------------------------------------------

--
-- Table structure for table `documents`
--

CREATE TABLE `documents` (
  `id` int(11) NOT NULL,
  `candidate_id` int(11) DEFAULT NULL,
  `doc_type` varchar(50) NOT NULL,
  `file_path` varchar(300) NOT NULL,
  `uploaded_at` datetime DEFAULT current_timestamp(),
  `file_hash` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `documents`
--

INSERT INTO `documents` (`id`, `candidate_id`, `doc_type`, `file_path`, `uploaded_at`, `file_hash`) VALUES
(73, NULL, 'driving_license', 'uploads/doc_6a05fb0f0f1e7.jpeg', '2026-05-14 18:40:47', 'f66032dee38964b7e624b49a232f1a23'),
(74, NULL, 'transcript', 'uploads/doc_6a05fba860c84.jpg', '2026-05-14 18:43:20', '16088595c9ea628b2cad5f64be829b36'),
(75, NULL, 'certificate', 'uploads/doc_6a05fc1b79f82.jpg', '2026-05-14 18:45:15', '57d944bc6e769c45b1fa39abc982d015'),
(76, NULL, 'national_id', 'uploads/doc_6a05fdaa3e9ce.jpg', '2026-05-14 18:51:54', 'a9ab60cde4ba372aabaebfb1dc20ff6c'),
(94, 11, 'certificate', 'uploads/doc_6a08b3de158f2.jpg', '2026-05-16 20:13:50', '68debb496d030399e6673dd03b691e93'),
(95, 11, 'certificate', 'uploads/doc_6a08b57f07162.jpg', '2026-05-16 20:20:47', '68debb496d030399e6673dd03b691e93'),
(137, 17, 'driving_license', 'uploads/doc_6a12dd8cc7002.jpeg', '2026-05-24 13:14:21', 'c10d3258205c6d0021bb74b7b7e302a8'),
(138, 18, 'driving_license', 'uploads/doc_6a12deff38501.jpeg', '2026-05-24 13:20:31', 'fe0c9d2d41a3bba2fe51ff8be9b96af8'),
(139, 18, 'driving_license', 'uploads/doc_6a12e0861a2e4.jpeg', '2026-05-24 13:27:02', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(144, 17, 'driving_license', 'uploads/doc_6a132e2a49101.jpeg', '2026-05-24 18:58:18', 'c10d3258205c6d0021bb74b7b7e302a8'),
(145, 17, 'driving_license', 'uploads/doc_6a132ea636a81.jpg', '2026-05-24 19:00:22', '0ec28818746c871f9312d45660b839fd'),
(149, 18, 'driving_license', 'uploads/doc_6a13657a69f50.jpeg', '2026-05-24 22:54:18', 'c10d3258205c6d0021bb74b7b7e302a8'),
(150, 18, 'driving_license', 'uploads/doc_6a1365fb4d405.jpeg', '2026-05-24 22:56:27', 'fe0c9d2d41a3bba2fe51ff8be9b96af8'),
(151, 18, 'driving_license', 'uploads/doc_6a1366270c7aa.jpeg', '2026-05-24 22:57:11', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(152, 18, 'driving_license', 'uploads/doc_6a136664ea4e7.jpeg', '2026-05-24 22:58:13', 'fe0c9d2d41a3bba2fe51ff8be9b96af8'),
(153, 18, 'driving_license', 'uploads/doc_6a136694841df.jpeg', '2026-05-24 22:59:00', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(154, 20, 'driving_license', 'uploads/doc_6a1367233183d.jpeg', '2026-05-24 23:01:23', 'c3ebb8e256d706f7ba18e2c1033568a3'),
(165, 18, 'driving_license', 'uploads/doc_6a14b392a3e10.jpeg', '2026-05-25 22:39:46', 'fe0c9d2d41a3bba2fe51ff8be9b96af8'),
(166, 18, 'driving_license', 'uploads/doc_6a14b543d63c9.jpeg', '2026-05-25 22:47:00', 'fe0c9d2d41a3bba2fe51ff8be9b96af8'),
(167, 18, 'driving_license', 'uploads/doc_6a14b61138cfb.jpeg', '2026-05-25 22:50:25', 'fe0c9d2d41a3bba2fe51ff8be9b96af8'),
(168, 18, 'driving_license', 'uploads/doc_6a14b69540cc9.jpeg', '2026-05-25 22:52:37', '1f665810a1430b1dbf2a3476d366725c'),
(169, 18, 'driving_license', 'uploads/doc_6a14b81aa549f.jpeg', '2026-05-25 22:59:06', '1f665810a1430b1dbf2a3476d366725c'),
(170, 18, 'driving_license', 'uploads/doc_6a14ba691a194.jpeg', '2026-05-25 23:08:57', '1f665810a1430b1dbf2a3476d366725c'),
(171, 18, 'driving_license', 'uploads/doc_6a1562d653ec7.jpeg', '2026-05-26 11:07:34', '1f665810a1430b1dbf2a3476d366725c'),
(172, 17, 'driving_license', 'uploads/doc_6a1563602c0d2.jpeg', '2026-05-26 11:09:52', 'c10d3258205c6d0021bb74b7b7e302a8'),
(173, 17, 'driving_license', 'uploads/doc_6a1563979c322.jpeg', '2026-05-26 11:10:47', 'c3ebb8e256d706f7ba18e2c1033568a3'),
(174, 17, 'driving_license', 'uploads/doc_6a1563cd26e6c.jpeg', '2026-05-26 11:11:41', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(178, 18, 'driving_license', 'uploads/doc_6a1b475b25603.jpeg', '2026-05-30 22:23:55', '1f665810a1430b1dbf2a3476d366725c'),
(179, 18, 'driving_license', 'uploads/doc_6a1b47b11fd11.jpeg', '2026-05-30 22:25:21', 'c3ebb8e256d706f7ba18e2c1033568a3'),
(180, 18, 'driving_license', 'uploads/doc_6a1b482249d4e.jpeg', '2026-05-30 22:27:14', 'c10d3258205c6d0021bb74b7b7e302a8'),
(181, 18, 'driving_license', 'uploads/doc_6a1b485211c9e.jpeg', '2026-05-30 22:28:02', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(186, 20, 'transcript', 'uploads/doc_6a1b4db78909d.jpg', '2026-05-30 22:51:03', 'bb7459b88db8bb348d0adba9248bfb91'),
(187, 20, 'other', 'uploads/doc_6a1b4e1aced46.png', '2026-05-30 22:52:43', '0586c12a156f762056f90e1712a5d05e'),
(188, 20, 'certificate', 'uploads/doc_6a1b4eb41837f.png', '2026-05-30 22:55:16', 'be87d5ab51bf9c16d520449fd11ebce2'),
(189, 20, 'certificate', 'uploads/doc_6a1b4efccd504.png', '2026-05-30 22:56:29', 'be87d5ab51bf9c16d520449fd11ebce2'),
(190, 20, 'certificate', 'uploads/doc_6a1b4fb7d3b12.png', '2026-05-30 22:59:36', '4d0dbb622d2a6667d82b1c4de95117e2'),
(212, 20, 'certificate', 'uploads/doc_6a1eb8ebcee5c.jpg', '2026-06-02 13:05:16', '86b8f8edd91d0ee42866ebbb5a921146'),
(216, 20, 'transcript', 'uploads/doc_6a1eba4e7d339.jpg', '2026-06-02 13:11:10', '86b8f8edd91d0ee42866ebbb5a921146'),
(220, 17, 'certificate', 'uploads/doc_6a1ec781b544a.jpg', '2026-06-02 14:07:29', '01c52d53022ac174f1cb0082e5049b78'),
(223, 22, 'certificate', 'uploads/doc_6a1ec97c2a487.jpg', '2026-06-02 14:15:56', '82129e46b0a06a867e298b1271034e62'),
(224, 22, 'certificate', 'uploads/doc_6a1ec9fb9633a.jpg', '2026-06-02 14:18:03', '82129e46b0a06a867e298b1271034e62'),
(225, 22, 'certificate', 'uploads/doc_6a1ecede1f03d.jpg', '2026-06-02 14:38:54', '82129e46b0a06a867e298b1271034e62'),
(227, 22, 'certificate', 'uploads/doc_6a1ed1af98d78.jpg', '2026-06-02 14:50:55', '82129e46b0a06a867e298b1271034e62'),
(228, 22, 'certificate', 'uploads/doc_6a1ed3113b8b4.jpg', '2026-06-02 14:56:49', '82129e46b0a06a867e298b1271034e62'),
(229, 22, 'certificate', 'uploads/doc_6a1ed477c97eb.jpg', '2026-06-02 15:02:48', '82129e46b0a06a867e298b1271034e62'),
(232, 22, 'certificate', 'uploads/doc_6a1edde83077d.jpg', '2026-06-02 15:43:04', '82129e46b0a06a867e298b1271034e62'),
(233, 22, 'certificate', 'uploads/doc_6a1edf47c9b7f.jpg', '2026-06-02 15:48:55', '82129e46b0a06a867e298b1271034e62'),
(255, 24, 'certificate', 'uploads/doc_6a1fe0ceedae4.jpg', '2026-06-03 10:07:43', '0f7435ad0dcd6a46cba5519219e183fb'),
(256, 24, 'certificate', 'uploads/doc_6a1fe55b26e16.jpg', '2026-06-03 10:27:07', '0f7435ad0dcd6a46cba5519219e183fb'),
(257, 24, 'certificate', 'uploads/doc_6a1fe8b8e80b2.jpg', '2026-06-03 10:41:29', '14351c8691becb39a15b63929e7773b2'),
(258, 25, 'national_id', 'uploads/doc_6a20779a1b141.jpg', '2026-06-03 20:51:06', '0fc55b92c233b70410dc8f6a65335729'),
(261, 26, 'certificate', 'uploads/doc_6a23bb70ef58c.jpg', '2026-06-06 08:17:21', 'c94d5112874cd4b8f03b67170aa9e404'),
(262, 26, 'transcript', 'uploads/doc_6a23bc6ec4291.jpg', '2026-06-06 08:21:35', '9c5f726478fe486921539a2547cfc535'),
(263, 26, 'transcript', 'uploads/doc_6a23bdbea4b69.jpg', '2026-06-06 08:27:10', '1a1d5accdb539d5c3a1f756e124173aa'),
(264, 25, 'transcript', 'uploads/doc_6a23bf5ba1c7b.jpg', '2026-06-06 08:34:03', 'bae64d6733302c13b43e738cb88a501e'),
(265, 25, 'transcript', 'uploads/doc_6a23c031de3b6.jpg', '2026-06-06 08:37:38', '57b57156b7d4eebff927251954671e87'),
(266, 25, 'transcript', 'uploads/doc_6a23c1a57d324.jpg', '2026-06-06 08:43:49', '0eb0c171b1e99024ae41ecde0b818629'),
(267, 25, 'transcript', 'uploads/doc_6a23c390a8948.jpg', '2026-06-06 08:52:01', '9c5f726478fe486921539a2547cfc535'),
(268, 25, 'transcript', 'uploads/doc_6a23c58e30389.jpg', '2026-06-06 09:00:30', '9c5f726478fe486921539a2547cfc535'),
(269, 25, 'driving_license', 'uploads/doc_6a23c792b4ba3.jpeg', '2026-06-06 09:09:06', '1f665810a1430b1dbf2a3476d366725c'),
(270, 18, 'driving_license', 'uploads/doc_6a23c885af283.jpeg', '2026-06-06 09:13:10', '1f665810a1430b1dbf2a3476d366725c'),
(271, 20, 'driving_license', 'uploads/doc_6a23c90665d8a.jpeg', '2026-06-06 09:15:18', 'c3ebb8e256d706f7ba18e2c1033568a3'),
(272, 17, 'driving_license', 'uploads/doc_6a23c9a302be0.jpeg', '2026-06-06 09:17:55', 'c10d3258205c6d0021bb74b7b7e302a8'),
(273, 27, 'driving_license', 'uploads/doc_6a23ca40e791a.jpeg', '2026-06-06 09:20:33', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(274, 18, 'driving_license', 'uploads/doc_6a23cb207638a.jpeg', '2026-06-06 09:24:16', 'e631ff68f0b3d55e8b59c7ba76beef54'),
(275, 28, 'driving_license', 'uploads/doc_6a23cc811685a.png', '2026-06-06 09:30:09', 'e51ae4ad4e1693e059e9c5183eea3820'),
(276, 28, 'national_id', 'uploads/doc_6a23ccffdde55.png', '2026-06-06 09:32:16', '0ee1741adca702a24dccb0d328c0d240'),
(277, 28, 'certificate', 'uploads/doc_6a23cd916b716.jpg', '2026-06-06 09:34:41', 'fe0b788ee10f88260a92aadbfe570f99'),
(278, 28, 'other', 'uploads/doc_6a23cebbb6c7d.png', '2026-06-06 09:39:39', '4d0dbb622d2a6667d82b1c4de95117e2'),
(279, 28, 'other', 'uploads/doc_6a23cf3363575.png', '2026-06-06 09:41:39', '31acd42e91735dabf0abcf20a33599f1'),
(280, 28, 'other', 'uploads/doc_6a23d031cf0fd.png', '2026-06-06 09:45:54', 'eb4347712d38bd09aaeed986c09ff10e'),
(281, 28, 'certificate', 'uploads/doc_6a23d0cb18217.png', '2026-06-06 09:48:27', 'eb4347712d38bd09aaeed986c09ff10e'),
(282, 28, 'other', 'uploads/doc_6a23d19464288.png', '2026-06-06 09:51:48', 'dc459d709f19c689ce8119d19e095967'),
(283, 28, 'other', 'uploads/doc_6a23d34e8e051.png', '2026-06-06 09:59:10', 'ee81e0ec03985bf055e68841981f3b48'),
(284, 28, 'transcript', 'uploads/doc_6a23d774498e9.jpg', '2026-06-06 10:16:52', 'b963302567bb733e956c86972cc49d01'),
(285, 28, 'certificate', 'uploads/doc_6a23d8bf36405.jpg', '2026-06-06 10:22:23', '6e64843799d6bc817a3410c00a0c41f2'),
(286, 28, 'transcript', 'uploads/doc_6a23d9f128b4c.jpg', '2026-06-06 10:27:29', '6e64843799d6bc817a3410c00a0c41f2'),
(287, 28, 'transcript', 'uploads/doc_6a23dac55c6fd.jpg', '2026-06-06 10:31:01', '33429e860f7c424516d671e525f650e8'),
(288, 28, 'transcript', 'uploads/doc_6a23dbbf46ef9.jpg', '2026-06-06 10:35:11', '49df7d64fb846678e06ede2530315741'),
(289, 28, 'transcript', 'uploads/doc_6a23dcf3e3995.jpg', '2026-06-06 10:40:20', 'c7dd10afe4640e64b98a3818de904516'),
(290, 28, 'transcript', 'uploads/doc_6a23e16d28b59.jpg', '2026-06-06 10:59:25', '33429e860f7c424516d671e525f650e8'),
(291, 28, 'certificate', 'uploads/doc_6a23e3fe426c8.jpg', '2026-06-06 11:10:22', '82129e46b0a06a867e298b1271034e62'),
(292, 28, 'certificate', 'uploads/doc_6a23ea61dfb72.jpg', '2026-06-06 11:37:38', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(293, 28, 'certificate', 'uploads/doc_6a23edf8d09eb.jpg', '2026-06-06 11:52:57', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(294, 28, 'certificate', 'uploads/doc_6a23f1782300f.jpg', '2026-06-06 12:07:52', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(295, 28, 'certificate', 'uploads/doc_6a23f2dab4ba3.jpg', '2026-06-06 12:13:47', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(296, 28, 'certificate', 'uploads/doc_6a23f4d371b36.jpg', '2026-06-06 12:22:11', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(297, 28, 'certificate', 'uploads/doc_6a23f86a350b8.jpg', '2026-06-06 12:37:30', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(298, 28, 'certificate', 'uploads/doc_6a23f941e60ae.jpg', '2026-06-06 12:41:06', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(299, 28, 'certificate', 'uploads/doc_6a23fa1db3e6f.jpg', '2026-06-06 12:44:46', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(300, 28, 'certificate', 'uploads/doc_6a23fba315430.jpg', '2026-06-06 12:51:15', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(301, 28, 'certificate', 'uploads/doc_6a23fc463ac24.jpg', '2026-06-06 12:53:58', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(302, 28, 'certificate', 'uploads/doc_6a23fe4316f38.jpg', '2026-06-06 13:02:27', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(303, 28, 'certificate', 'uploads/doc_6a23ff6fed7f8.jpg', '2026-06-06 13:07:28', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(304, 28, 'certificate', 'uploads/doc_6a24004278d2c.jpg', '2026-06-06 13:10:58', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(305, 28, 'certificate', 'uploads/doc_6a24012ba2e48.jpg', '2026-06-06 13:14:52', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(306, 28, 'certificate', 'uploads/doc_6a2402b10c4ba.jpg', '2026-06-06 13:21:21', '788807dc4a7176c45eb1b06ad634376c'),
(307, 28, 'certificate', 'uploads/doc_6a2404b0f1676.jpg', '2026-06-06 13:29:53', '2efd71099f9b059ddc6cd1a3cb65d06a'),
(328, 28, 'certificate', 'uploads/doc_6a24229beca8b.jpg', '2026-06-06 15:37:32', 'ef03e2499c1dc4f063b24c39bb0f77f4'),
(329, 28, 'certificate', 'uploads/doc_6a24238da21a0.jpeg', '2026-06-06 15:41:33', '48d8e8b598a71aa1ae72310346521c9b'),
(357, 30, 'certificate', 'uploads/doc_6a2721d27635e.jpg', '2026-06-08 22:10:58', 'a5b35dda316eb0145afad95d4b577498'),
(358, 31, 'certificate', 'uploads/doc_6a2722ad01c5c.jpg', '2026-06-08 22:14:37', 'eca5b830746aa44df169dc078ecc8900'),
(359, 30, 'certificate', 'uploads/doc_6a27245fc3895.jpg', '2026-06-08 22:21:52', 'a5b35dda316eb0145afad95d4b577498'),
(360, 32, 'certificate', 'uploads/doc_6a2724e963fcc.jpg', '2026-06-08 22:24:09', 'a5b35dda316eb0145afad95d4b577498'),
(361, 33, 'certificate', 'uploads/doc_6a2725d3d6ff3.jpg', '2026-06-08 22:28:04', 'e6c9976a8a9f6eabe69eeb4aa7881135'),
(362, 33, 'certificate', 'uploads/doc_6a2726a5d0dc7.jpg', '2026-06-08 22:31:34', 'e6c9976a8a9f6eabe69eeb4aa7881135'),
(363, 22, 'certificate', 'uploads/doc_6a272879717f0.jpg', '2026-06-08 22:39:21', '82129e46b0a06a867e298b1271034e62'),
(364, 33, 'certificate', 'uploads/doc_6a286eadcc8b2.jpg', '2026-06-09 21:51:10', 'e6c9976a8a9f6eabe69eeb4aa7881135'),
(365, 33, 'certificate', 'uploads/doc_6a28703a2c711.jpg', '2026-06-09 21:57:46', 'e6c9976a8a9f6eabe69eeb4aa7881135'),
(366, 30, 'certificate', 'uploads/doc_6a2870a6bbac5.jpg', '2026-06-09 21:59:35', 'a5b35dda316eb0145afad95d4b577498'),
(369, 28, 'certificate', 'uploads/doc_6a28720ceae7d.jpg', '2026-06-09 22:05:33', '20e69ba3751e534929994b835a7f2e07'),
(370, 34, 'certificate', 'uploads/doc_6a28737a3cefe.png', '2026-06-09 22:11:38', '98a11cb1fa2cfd8ff59ad0bc28c5e647'),
(371, 34, 'certificate', 'uploads/doc_6a2877014f47b.jpg', '2026-06-09 22:26:41', '3672225a17b32009599e650f026ab05e'),
(372, 34, 'certificate', 'uploads/doc_6a28780e74f01.png', '2026-06-09 22:31:10', '98a11cb1fa2cfd8ff59ad0bc28c5e647'),
(373, 34, 'certificate', 'uploads/doc_6a287995b1cb5.jpg', '2026-06-09 22:37:41', 'b8574b6eab5cf41217363f78f6f83539'),
(374, 35, 'certificate', 'uploads/doc_6a2880a020339.jpg', '2026-06-09 23:07:44', '3672225a17b32009599e650f026ab05e'),
(375, 34, 'certificate', 'uploads/doc_6a2881c173323.jpg', '2026-06-09 23:12:33', '3672225a17b32009599e650f026ab05e'),
(376, 34, 'certificate', 'uploads/doc_6a28842a5682a.jpg', '2026-06-09 23:22:50', '3672225a17b32009599e650f026ab05e'),
(377, 34, 'certificate', 'uploads/doc_6a28850309985.jpg', '2026-06-09 23:26:27', 'e62a281d9e8896a3d7aa4f86c93c4b68'),
(378, 34, 'certificate', 'uploads/doc_6a2885aa22080.png', '2026-06-09 23:29:14', '98a11cb1fa2cfd8ff59ad0bc28c5e647'),
(379, 34, 'certificate', 'uploads/doc_6a28867c8964f.jpg', '2026-06-09 23:32:44', 'e62a281d9e8896a3d7aa4f86c93c4b68'),
(380, 34, 'transcript', 'uploads/doc_6a288a147d889.jpg', '2026-06-09 23:48:04', '9d3f2c7c384c32f857488202e65bd271'),
(381, 34, 'certificate', 'uploads/doc_6a288bddcd3cc.jpg', '2026-06-09 23:55:42', 'e62a281d9e8896a3d7aa4f86c93c4b68'),
(382, 34, 'certificate', 'uploads/doc_6a288c7c98da1.jpg', '2026-06-09 23:58:20', '3672225a17b32009599e650f026ab05e'),
(383, 34, 'certificate', 'uploads/doc_6a288d7c99cb4.png', '2026-06-10 00:02:36', 'bb132f1e32cc9ccb7037b40d515a518f'),
(384, 34, 'certificate', 'uploads/doc_6a288e471546b.png', '2026-06-10 00:05:59', '98a11cb1fa2cfd8ff59ad0bc28c5e647'),
(385, 34, 'certificate', 'uploads/doc_6a28faf340c4f.png', '2026-06-10 07:49:39', '85421383b573147586ecf2e115f32d03'),
(386, 34, 'certificate', 'uploads/doc_6a28fc0e8dfd8.jpg', '2026-06-10 07:54:22', 'e62a281d9e8896a3d7aa4f86c93c4b68'),
(387, 36, 'certificate', 'uploads/doc_6a28fdc730b66.png', '2026-06-10 08:01:43', '2230411b3235e0b4f1c2e1ac52f6f7ef'),
(388, 36, 'certificate', 'uploads/doc_6a28fe55330d8.jpg', '2026-06-10 08:04:05', 'e62a281d9e8896a3d7aa4f86c93c4b68'),
(389, 36, 'certificate', 'uploads/doc_6a28feffbe56b.png', '2026-06-10 08:06:56', '871a6fd45f3f9b2242e90602396ad871'),
(390, 22, 'certificate', 'uploads/doc_6a2900cda7c79.jpg', '2026-06-10 08:14:37', '82129e46b0a06a867e298b1271034e62'),
(391, 28, 'certificate', 'uploads/doc_6a29010c47ef9.jpg', '2026-06-10 08:15:40', '82129e46b0a06a867e298b1271034e62'),
(392, 28, 'certificate', 'uploads/doc_6a290267a8305.png', '2026-06-10 08:21:27', 'f6487e30515232ba71be63b8a230ca93'),
(393, 28, 'certificate', 'uploads/doc_6a2903adcbcc6.png', '2026-06-10 08:26:54', '1548219331d209743806b784a7cc73ef'),
(394, 31, 'certificate', 'uploads/doc_6a29052c03aa7.jpg', '2026-06-10 08:33:16', 'eca5b830746aa44df169dc078ecc8900'),
(395, 31, 'certificate', 'uploads/doc_6a2906c3a9b54.jpg', '2026-06-10 08:40:04', '6f9a5598d22716bbdf0d0aa6a18c99f6'),
(396, 31, 'certificate', 'uploads/doc_6a290c48dc8a8.jpg', '2026-06-10 09:03:37', 'eca5b830746aa44df169dc078ecc8900'),
(397, 31, 'certificate', 'uploads/doc_6a290e0f13165.jpg', '2026-06-10 09:11:11', 'eca5b830746aa44df169dc078ecc8900'),
(398, 31, 'certificate', 'uploads/doc_6a290ef1c67ba.jpg', '2026-06-10 09:14:58', '6f9a5598d22716bbdf0d0aa6a18c99f6'),
(399, 31, 'certificate', 'uploads/doc_6a290ff7d111d.jpg', '2026-06-10 09:19:20', 'a91686dd7601ba360d6fcd62af9bcca7'),
(400, 31, 'certificate', 'uploads/doc_6a2911c78b441.png', '2026-06-10 09:27:03', '1548219331d209743806b784a7cc73ef'),
(401, 31, 'certificate', 'uploads/doc_6a2912f0aa3e9.jpeg', '2026-06-10 09:32:00', '5903031ba0f651fd7dd5ace1d510dde6');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','hr') DEFAULT 'hr',
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `created_at`) VALUES
(1, 'Admin', 'admin@docverify.rw', '$2y$10$VrllXrF4n2wZ3vHcoOJgqeMWIxtA2g9AzGI8tLLrpom5KAteoszyi', 'admin', '2026-05-11 18:16:41'),
(2, 'MUKESHIMANA Delphine', 'delphinemuke3@gmail.com', '$2y$10$A4fKiJQk25gnS17kJc0hQ.xVb5cp7NDnh4lUnzrin5XBb9hOwYXK2', 'hr', '2026-05-26 17:38:36');

-- --------------------------------------------------------

--
-- Table structure for table `verifications`
--

CREATE TABLE `verifications` (
  `id` int(11) NOT NULL,
  `candidate_id` int(11) DEFAULT NULL,
  `document_id` int(11) NOT NULL,
  `authenticity_score` int(11) DEFAULT 0,
  `status` varchar(20) DEFAULT 'Pending',
  `issues` text DEFAULT NULL,
  `recommendation` text DEFAULT NULL,
  `verified_at` datetime DEFAULT NULL,
  `qr_url` varchar(500) DEFAULT NULL,
  `qr_institution` varchar(255) DEFAULT NULL,
  `qr_verified` tinyint(1) DEFAULT 0,
  `name_match` tinyint(1) DEFAULT NULL,
  `cert_holder` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `verifications`
--

INSERT INTO `verifications` (`id`, `candidate_id`, `document_id`, `authenticity_score`, `status`, `issues`, `recommendation`, `verified_at`, `qr_url`, `qr_institution`, `qr_verified`, `name_match`, `cert_holder`) VALUES
(73, NULL, 73, 0, 'Fake', 'Document type mismatch: selected \'driving_license\' expects license, but model detected Rwanda National Identification Card (id) at 88.4% confidence.; Document type mismatch: selected Driving license expects license, but model detected Rwanda National Identification Card (id) at 88.4% confidence.', 'The trained model result does not match the selected document type. Document was not marked valid.', '2026-05-14 18:40:57', NULL, NULL, 0, NULL, NULL),
(74, NULL, 74, 0, 'Fake', 'Document type mismatch: selected \'transcript\' expects transcript, but model detected National Examination and School Inspection Certificate (certificate) at 99.2% confidence.; Document type mismatch: selected Transcript expects transcript, but model detected National Examination and School Inspection Certificate (certificate) at 99.2% confidence.', 'The trained model result does not match the selected document type. Document was not marked valid.', '2026-05-14 18:43:30', NULL, NULL, 0, NULL, NULL),
(75, NULL, 75, 100, 'Verified', '', 'Document matches trained model class: NESA Certificate. Description: National Examination and School Inspection Certificate. Confidence: 84.7%. Marked valid at 100%. Candidate may proceed.', '2026-05-14 18:45:25', NULL, NULL, 0, NULL, NULL),
(76, NULL, 76, 100, 'Verified', '', 'Document matches trained model class: Rwanda National ID. Description: Rwanda National Identification Card. Confidence: 97.7%. Marked valid at 100%. Candidate may proceed.', '2026-05-14 18:52:04', NULL, NULL, 0, NULL, NULL),
(94, 11, 94, 100, 'Verified', '', 'Document matches trained model class: MKU Degree. Description: Mount Kenya University Degree Certificate. Confidence: 99.7%. Marked valid at 100%. Candidate may proceed.', '2026-05-16 20:14:09', NULL, NULL, 0, NULL, NULL),
(95, 11, 95, 100, 'Verified', '', 'Document matches trained model class: MKU Degree. Description: Mount Kenya University Degree Certificate. Confidence: 99.7%. Marked valid at 100%. Candidate may proceed.', '2026-05-16 20:21:06', NULL, NULL, 0, NULL, NULL),
(137, 17, 137, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 84.4%. Marked valid at 100%. Candidate may proceed.', '2026-05-24 13:14:37', NULL, NULL, 0, NULL, NULL),
(138, 18, 138, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-24 13:20:52', NULL, NULL, 0, NULL, NULL),
(139, 18, 139, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 79.9%. Marked valid at 100%. Candidate may proceed.', '2026-05-24 13:27:21', NULL, NULL, 0, NULL, NULL),
(144, 17, 144, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 84.4%. Marked valid at 100%. Candidate may proceed.', '2026-05-24 18:58:36', NULL, NULL, 0, NULL, NULL),
(145, 17, 145, 0, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'BENURUGO Cesar\' (doc ID: 141). This is a strong indicator of a borrowed or shared certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-24 19:00:41', NULL, NULL, 0, NULL, NULL),
(149, 18, 149, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'MBABAZI Diane\' (doc ID: 137). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'MBABAZI Diane\'. This is a borrowed certificate. Reject this application.', '2026-05-24 22:54:26', NULL, NULL, 0, NULL, NULL),
(150, 18, 150, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-24 22:56:35', NULL, NULL, 0, NULL, NULL),
(151, 18, 151, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 79.9%. Marked valid at 100%. Candidate may proceed.', '2026-05-24 22:57:19', NULL, NULL, 0, NULL, NULL),
(152, 18, 152, 0, 'Fake', 'Trained model did not detect a known document class', 'Document detected as Rwanda Driving License at 19.2% confidence (minimum required: 20.0%). Please upload a clear, flat, well-lit scan of the front of the document.', '2026-05-25 15:43:13', NULL, NULL, 0, NULL, NULL),
(154, 20, 154, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-24 23:01:31', NULL, NULL, 0, NULL, NULL),
(165, 18, 165, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-25 22:39:58', NULL, NULL, 0, NULL, NULL),
(166, 18, 166, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-25 22:47:11', NULL, NULL, 0, NULL, NULL),
(167, 18, 167, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-25 22:50:37', NULL, NULL, 0, NULL, NULL),
(168, 18, 168, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-25 22:52:49', NULL, NULL, 0, NULL, NULL),
(169, NULL, 153, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Confidence: 79.9% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-05-25 22:58:21', NULL, NULL, 0, NULL, NULL),
(170, 18, 169, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-25 22:59:18', NULL, NULL, 0, NULL, NULL),
(171, 18, 170, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-25 23:09:08', NULL, NULL, 0, NULL, NULL),
(172, 18, 171, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-26 11:07:50', NULL, NULL, 0, NULL, NULL),
(173, 17, 172, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 84.4% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-05-26 11:10:08', NULL, NULL, 0, NULL, NULL),
(174, 17, 173, 0, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IMANISHIMWE Nadine\' (doc ID: 154). This is a strong indicator of a borrowed or shared certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-26 11:11:03', NULL, NULL, 0, NULL, NULL),
(175, 17, 174, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IZIBIDUKWIYE Kevin\' (doc ID: 139). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IZIBIDUKWIYE Kevin\'. This is a borrowed certificate. Reject this application.', '2026-05-26 11:12:01', NULL, NULL, 0, NULL, NULL),
(179, 18, 178, 0, 'Fake', 'Type mismatch: expected license, got Rwanda National Identification Card (id) at 76.6%.; Document type mismatch: selected Driving license expects license, but model detected Rwanda National Identification Card (id) at 76.6% confidence.', 'The trained model result does not match the selected document type. Document was not marked valid.', '2026-05-30 22:24:15', NULL, NULL, 0, NULL, NULL),
(180, 18, 179, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IMANISHIMWE Nadine\' (doc ID: 154). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IMANISHIMWE Nadine\'. This is a borrowed certificate. Reject this application.', '2026-05-30 22:25:40', NULL, NULL, 0, NULL, NULL),
(181, 18, 180, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'MBABAZI Diane\' (doc ID: 137). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'MBABAZI Diane\'. This is a borrowed certificate. Reject this application.', '2026-05-30 22:27:32', NULL, NULL, 0, NULL, NULL),
(182, 18, 181, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-30 22:28:19', NULL, NULL, 0, NULL, NULL),
(187, 20, 186, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-05-30 22:51:23', NULL, NULL, 0, NULL, NULL),
(188, 20, 187, 0, 'Fake', 'Low-confidence detection: Universite Libre de Kigali Degree Certificate (71.6%, required 40%).; Selected document type \'other\' cannot be automatically verified against model class ULK Degree.', 'The trained model result does not match the selected document type. Document was not marked valid.', '2026-05-30 22:52:59', NULL, NULL, 0, NULL, NULL),
(189, 20, 188, 100, 'Verified', '', 'Document matches trained model class: NESA Certificate. Description: National Examination and School Inspection Certificate. Confidence: 80.5% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-05-30 22:55:32', NULL, NULL, 0, NULL, NULL),
(190, 20, 189, 100, 'Verified', '', 'Document matches trained model class: NESA Certificate. Description: National Examination and School Inspection Certificate. Confidence: 80.5% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-05-30 22:56:44', NULL, NULL, 0, NULL, NULL),
(191, 20, 190, 100, 'Verified', '', 'Document matches trained model class: ULK Degree. Description: Universite Libre de Kigali Degree Certificate. Confidence: 88.6% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-05-30 22:59:51', NULL, NULL, 0, NULL, NULL),
(213, 20, 212, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-02 13:05:30', NULL, NULL, 0, NULL, NULL),
(217, 20, 216, 100, 'Verified', '', 'Document matches trained model class: UTAB Transcript. Description: University of Technology and Arts of Byumba Academic Transcript. Confidence: 41.1% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-02 13:11:25', NULL, NULL, 0, NULL, NULL),
(221, 17, 220, 100, 'Verified', '', 'Document matches trained model class: NESA Certificate. Description: National Examination and School Inspection Certificate. Confidence: 90.9% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-02 14:07:47', NULL, NULL, 0, NULL, NULL),
(224, 22, 223, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IRADUKUNDA James\' (doc ID: 217). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IRADUKUNDA James\'. This is a borrowed certificate. Reject this application.', '2026-06-02 14:16:11', NULL, NULL, 0, NULL, NULL),
(225, 22, 224, 100, 'Verified', '', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 93.9% (required 40%). QR verified online at University of Technology and Arts of Byumba. Marked valid at 100%. Candidate may proceed.', '2026-06-02 14:18:18', NULL, NULL, 0, NULL, NULL),
(226, 22, 225, 100, 'Verified', '', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 93.9% (required 40%). QR verified online at University of Technology and Arts of Byumba. Marked valid at 100%. Candidate may proceed.', '2026-06-02 14:39:11', NULL, NULL, 0, NULL, NULL),
(228, 22, 227, 100, 'Verified', '', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 93.9% (required 40%). QR verified online at University of Technology and Arts of Byumba. Marked valid at 100%. Candidate may proceed.', '2026-06-02 14:51:16', NULL, NULL, 0, NULL, NULL),
(229, 22, 228, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'FOR OTHER INFORMATION PLEASE CONTACT\' — DOES NOT MATCH candidate \'IRADUKUNDA Lambert\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-02 14:57:06', NULL, NULL, 0, NULL, NULL),
(230, 22, 229, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'FOR OTHER INFORMATION PLEASE CONTACT\' — DOES NOT MATCH candidate \'IRADUKUNDA Lambert\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-02 15:03:05', NULL, NULL, 0, NULL, NULL),
(233, 22, 232, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'FOR OTHER INFORMATION PLEASE CONTACT\' — DOES NOT MATCH candidate \'IRADUKUNDA Lambert\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-02 15:43:21', NULL, NULL, 0, NULL, NULL),
(234, 22, 233, 100, 'Verified', '', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 93.9% (required 40%). QR verified online at University of Technology and Arts of Byumba. Marked valid at 100%. Candidate may proceed.', '2026-06-02 15:49:11', NULL, NULL, 0, NULL, NULL),
(256, 24, 255, 90, 'Verified', '', 'Document matches trained model class: UR Degree. Description: University of Rwanda Degree Certificate. Confidence: 58.7% (required 40%). Some issues detected — manual review recommended.', '2026-06-03 10:08:30', NULL, NULL, 0, NULL, NULL),
(257, 24, 256, 90, 'Verified', '', 'Document matches trained model class: UR Degree. Description: University of Rwanda Degree Certificate. Confidence: 58.7% (required 40%). Some issues detected — manual review recommended.', '2026-06-03 10:27:50', NULL, NULL, 0, NULL, NULL),
(258, 24, 257, 90, 'Verified', '', 'Document matches trained model class: UR Degree. Description: University of Rwanda Degree Certificate. Confidence: 92.6% (required 40%). Some issues detected — manual review recommended.', '2026-06-03 10:42:22', NULL, NULL, 0, NULL, NULL),
(259, 25, 258, 100, 'Verified', '', 'Document matches trained model class: Rwanda National ID. Description: Rwanda National Identification Card. Confidence: 85.4% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-03 20:53:30', NULL, NULL, 0, NULL, NULL),
(262, 26, 261, 100, 'Verified', '', 'Document matches trained model class: ULK Degree. Description: Universite Libre de Kigali Degree Certificate. Confidence: 97.2% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 08:19:12', NULL, NULL, 0, NULL, NULL),
(263, 26, 262, 90, 'Verified', '', 'Document matches trained model class: UR Transcript. Description: University of Rwanda Academic Transcript. Confidence: 55.9% (required 40%). Some issues detected — manual review recommended.', '2026-06-06 08:23:18', NULL, NULL, 0, NULL, NULL),
(264, 26, 263, 100, 'Verified', '', 'Document matches trained model class: ULK Transcript. Description: Universite Libre de Kigali Academic Transcript. Confidence: 82.9% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 08:28:46', NULL, NULL, 0, NULL, NULL),
(265, 25, 264, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 08:35:29', NULL, NULL, 0, NULL, NULL),
(266, 25, 265, 90, 'Verified', '', 'Document matches trained model class: ULK Transcript. Description: Universite Libre de Kigali Academic Transcript. Confidence: 80.6% (required 40%). Some issues detected — manual review recommended.', '2026-06-06 08:39:08', NULL, NULL, 0, NULL, NULL),
(267, 25, 266, 100, 'Verified', '', 'Document matches trained model class: ULK Transcript. Description: Universite Libre de Kigali Academic Transcript. Confidence: 51.5% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 08:45:27', NULL, NULL, 0, NULL, NULL),
(268, 25, 267, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'UWIRINGIYIMANA Elie\' (doc ID: 262). This is a strong indicator of a borrowed or shared certificate!; MKU QR detected but certificate number not found; QR links to unrecognized domain (-10 penalty)', 'DUPLICATE DOCUMENT: This file was previously submitted by \'UWIRINGIYIMANA Elie\'. This is a borrowed certificate. Reject this application.', '2026-06-06 08:53:57', NULL, NULL, 0, NULL, NULL),
(269, 25, 268, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'UWIRINGIYIMANA Elie\' (doc ID: 262). This is a strong indicator of a borrowed or shared certificate!; MKU QR detected but certificate number not found; QR links to unrecognized domain (-10 penalty)', 'DUPLICATE DOCUMENT: This file was previously submitted by \'UWIRINGIYIMANA Elie\'. This is a borrowed certificate. Reject this application.', '2026-06-06 09:02:46', NULL, NULL, 0, NULL, NULL),
(270, 25, 269, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IZIBIDUKWIYE Kevin\' (doc ID: 168). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IZIBIDUKWIYE Kevin\'. This is a borrowed certificate. Reject this application.', '2026-06-06 09:09:51', NULL, NULL, 0, NULL, NULL),
(271, 18, 270, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 93.9% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:13:52', NULL, NULL, 0, NULL, NULL),
(272, 20, 271, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 75.3% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:16:17', NULL, NULL, 0, NULL, NULL),
(273, 17, 272, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 95.9% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:18:39', NULL, NULL, 0, NULL, NULL),
(274, 27, 273, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IZIBIDUKWIYE Kevin\' (doc ID: 139). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IZIBIDUKWIYE Kevin\'. This is a borrowed certificate. Reject this application.', '2026-06-06 09:21:09', NULL, NULL, 0, NULL, NULL),
(275, 18, 274, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 87.3% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:24:53', NULL, NULL, 0, NULL, NULL),
(276, 28, 275, 100, 'Verified', '', 'Document matches trained model class: Rwanda Driving License. Description: Rwanda Driving License. Confidence: 90.6% (required 30%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:30:46', NULL, NULL, 0, NULL, NULL),
(277, 28, 276, 100, 'Verified', '', 'Document matches trained model class: Rwanda National ID. Description: Rwanda National Identification Card. Confidence: 85.8% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:33:01', NULL, NULL, 0, NULL, NULL),
(278, 28, 277, 0, 'Fake', 'Online check: Certificate not found in institution records — possible fake or altered document; QR links to unrecognized domain (-10 penalty); No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 09:36:25', NULL, NULL, 0, NULL, NULL),
(279, 28, 278, 0, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IMANISHIMWE Nadine\' (doc ID: 190). This is a strong indicator of a borrowed or shared certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 09:40:13', NULL, NULL, 0, NULL, NULL),
(280, 28, 279, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 09:42:18', NULL, NULL, 0, NULL, NULL),
(281, 28, 280, 0, 'Fake', 'Low-confidence detection: Rwanda Polytechnic Degree Certificate (95.2%, required 40%).; Selected document type \'other\' cannot be automatically verified against model class RP Degree.', 'The trained model result does not match the selected document type. Document was not marked valid.', '2026-06-06 09:46:33', NULL, NULL, 0, NULL, NULL),
(282, 28, 281, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 95.2% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 09:49:06', NULL, NULL, 0, NULL, NULL),
(283, 28, 282, 0, 'Fake', 'Name mismatch from QR link: QR shows \'LEADERDECEMODULE BYUKUSENGEINNOCENT OBJECTDETECTED\' but candidate is \'JACKY\'; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 09:52:30', NULL, NULL, 0, NULL, NULL),
(284, 28, 283, 0, 'Fake', 'No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 09:59:54', NULL, NULL, 0, NULL, NULL),
(285, 28, 284, 90, 'Verified', '', 'Document matches trained model class: ULK Transcript. Description: Universite Libre de Kigali Academic Transcript. Confidence: 64.1% (required 40%). Some issues detected — manual review recommended.', '2026-06-06 10:18:11', NULL, NULL, 0, NULL, NULL),
(286, 28, 285, 0, 'Fake', 'Type mismatch: expected certificate, degree, got University of Rwanda Academic Transcript (transcript) at 96.4%.; Document type mismatch: selected Certificate expects certificate, degree, but model detected University of Rwanda Academic Transcript (transcript) at 96.4% confidence.', 'The trained model result does not match the selected document type. Document was not marked valid.', '2026-06-06 10:23:57', NULL, NULL, 0, NULL, NULL),
(287, 28, 286, 100, 'Verified', '', 'Document matches trained model class: UR Transcript. Description: University of Rwanda Academic Transcript. Confidence: 96.4% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 10:29:07', NULL, NULL, 0, NULL, NULL),
(288, 28, 287, 100, 'Verified', '', 'Document matches trained model class: UR Transcript. Description: University of Rwanda Academic Transcript. Confidence: 96.5% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 10:32:17', NULL, NULL, 0, NULL, NULL),
(289, 28, 288, 100, 'Verified', '', 'Document matches trained model class: UR Transcript. Description: University of Rwanda Academic Transcript. Confidence: 88.8% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 10:36:39', NULL, NULL, 0, NULL, NULL),
(290, 28, 289, 100, 'Verified', '', 'Document matches trained model class: UR Transcript. Description: University of Rwanda Academic Transcript. Confidence: 98.1% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 10:41:46', NULL, NULL, 0, NULL, NULL),
(291, 28, 290, 100, 'Verified', '', 'Document matches trained model class: UR Transcript. Description: University of Rwanda Academic Transcript. Confidence: 96.5% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 11:00:43', NULL, NULL, 0, NULL, NULL),
(292, 28, 291, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IRADUKUNDA Lambert\' (doc ID: 223). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH ONLINE: Name on certificate: \'IRADUKUNDA LAMBERT\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IRADUKUNDA Lambert\'. This is a borrowed certificate. Reject this application.', '2026-06-06 11:10:44', NULL, NULL, 0, NULL, NULL),
(293, 28, 292, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-06 11:39:49', NULL, NULL, 0, NULL, NULL),
(294, 28, 293, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 11:53:36', NULL, NULL, 0, NULL, NULL),
(295, 28, 294, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'MBARUSHIMANA DANNY\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-06 12:08:29', NULL, NULL, 0, NULL, NULL),
(296, 28, 295, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'MBARUSHIMANA DANNY\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-06 12:14:23', NULL, NULL, 0, NULL, NULL),
(297, 28, 296, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 12:23:06', NULL, NULL, 0, NULL, NULL),
(298, 28, 297, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 12:38:24', NULL, NULL, 0, NULL, NULL),
(299, 28, 298, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 12:42:02', NULL, NULL, 0, NULL, NULL),
(300, 28, 299, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 12:45:38', NULL, NULL, 0, NULL, NULL),
(301, 28, 300, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 12:52:08', NULL, NULL, 0, NULL, NULL),
(302, 28, 301, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 12:54:51', NULL, NULL, 0, NULL, NULL),
(303, 28, 302, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'MBARUSHIMANA DANNY\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-06 13:03:20', NULL, NULL, 0, NULL, NULL),
(304, 28, 303, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'MBARUSHIMANA DANNY\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-06 13:08:21', NULL, NULL, 0, NULL, NULL),
(305, 28, 304, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 13:11:52', NULL, NULL, 0, NULL, NULL),
(306, 28, 305, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'MBARUSHIMANA DANNY\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-06 13:16:03', NULL, NULL, 0, NULL, NULL),
(307, 28, 306, 0, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'HIRWA Fabrice\' (doc ID: 193). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH ONLINE: Name on certificate: \'UMURERWA CLARISSE\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-06 13:22:20', NULL, NULL, 0, NULL, NULL),
(308, 28, 307, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'HIRWA Fabrice\' (doc ID: 192). This is a strong indicator of a borrowed or shared certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'HIRWA Fabrice\'. This is a borrowed certificate. Reject this application.', '2026-06-06 13:30:56', NULL, NULL, 0, NULL, NULL),
(329, 28, 328, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 96.7% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-06 15:38:17', NULL, NULL, 0, NULL, NULL),
(330, 28, 329, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'NIYIGENA SARAH\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-06 15:42:01', NULL, NULL, 0, NULL, NULL),
(358, 30, 357, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'TUMWINE Eric\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-08 22:11:55', NULL, NULL, 0, NULL, NULL),
(359, 31, 358, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 97.1% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-08 22:18:27', NULL, NULL, 0, NULL, NULL),
(360, 30, 359, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'TUMWINE Eric\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-08 22:22:47', NULL, NULL, 0, NULL, NULL),
(361, 32, 360, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'TUMWINE Eric\' (doc ID: 357). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'TUMWINE\' — possible borrowed certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'TUMWINE Eric\'. This is a borrowed certificate. Reject this application.', '2026-06-08 22:25:05', NULL, NULL, 0, NULL, NULL),
(362, 33, 361, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'HIRWA Fabrice\' (doc ID: 323). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH: Certificate shows \'BON COMMUNICATIONTE GHNOLOGYSTE SEE\' but candidate is \'NZAYISENGA Emmanuel\' — possible borrowed certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'HIRWA Fabrice\'. This is a borrowed certificate. Reject this application.', '2026-06-08 22:28:54', NULL, NULL, 0, NULL, NULL),
(363, 33, 362, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'ESESAD VANGED DIPLOMACIN INFORMATIONAND\' but candidate is \'NZAYISENGA Emmanuel\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-08 22:32:23', NULL, NULL, 0, NULL, NULL),
(364, 22, 363, 100, 'Verified', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'IRADUKUNDA Lambert\' — possible borrowed certificate!', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 97.2% (required 40%). QR verified online at University of Technology and Arts of Byumba. Marked valid at 100%. Candidate may proceed.', '2026-06-08 22:39:53', NULL, NULL, 0, NULL, NULL),
(365, 33, 364, 100, 'Verified', '⚠ NAME MISMATCH: Certificate shows \'BON COMMUNICATIONTE GHNOLOGYSTE SEE\' but candidate is \'NZAYISENGA Emmanuel\' — possible borrowed certificate!', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 98.4% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-09 21:52:22', NULL, NULL, 0, NULL, NULL),
(366, 33, 365, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 98.4% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-09 21:58:23', NULL, NULL, 0, NULL, NULL),
(367, 30, 366, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 99.3% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-09 22:00:04', NULL, NULL, 0, NULL, NULL),
(370, 28, 369, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'JACKY\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 22:07:07', NULL, NULL, 0, NULL, NULL),
(371, 34, 370, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 22:12:38', NULL, NULL, 0, NULL, NULL),
(372, 34, 371, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'NIYIGENA Sarah\' (doc ID: 337). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'NIYIGENA Sarah\'. This is a borrowed certificate. Reject this application.', '2026-06-09 22:28:24', NULL, NULL, 0, NULL, NULL),
(373, 34, 372, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 22:32:09', NULL, NULL, 0, NULL, NULL),
(374, 34, 373, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 22:38:57', NULL, NULL, 0, NULL, NULL),
(375, 35, 374, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'HASHIMWE Janvier\' (doc ID: 371). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH: Certificate shows \'AHISHAKIYE PATRICK\' but candidate is \'NIYIGENA Sarah\' — possible borrowed certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'HASHIMWE Janvier\'. This is a borrowed certificate. Reject this application.', '2026-06-09 23:09:44', NULL, NULL, 0, NULL, NULL),
(376, 34, 375, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'AHISHAKIYE PATRICK\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:15:08', NULL, NULL, 0, NULL, NULL),
(377, 34, 376, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'AHISHAKIYE PATRICK\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:24:26', NULL, NULL, 0, NULL, NULL),
(378, 34, 377, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'FOT BAHT ANY\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:27:33', NULL, NULL, 0, NULL, NULL),
(379, 34, 378, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:30:28', NULL, NULL, 0, NULL, NULL),
(380, 34, 379, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'FOT BAHT ANY\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:33:50', NULL, NULL, 0, NULL, NULL),
(381, 34, 380, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'ACADEMIC TRANSCRIOT\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:50:22', NULL, NULL, 0, NULL, NULL),
(382, 34, 381, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'FOT BAHT ANY\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:56:42', NULL, NULL, 0, NULL, NULL),
(383, 34, 382, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'AHISHAKIYE PATRICK\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-09 23:59:50', NULL, NULL, 0, NULL, NULL),
(384, 34, 383, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-10 00:03:40', NULL, NULL, 0, NULL, NULL),
(385, 34, 384, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'another person\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-10 00:07:07', NULL, NULL, 0, NULL, NULL),
(386, 34, 385, 100, 'Verified', '', 'Document matches trained model class: UR Degree. Description: University of Rwanda Degree Certificate. Confidence: 98.6% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-10 07:50:58', NULL, NULL, 0, NULL, NULL),
(387, 34, 386, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'FOT BAHT ANY\' but candidate is \'HASHIMWE Janvier\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-10 07:55:08', NULL, NULL, 0, NULL, NULL),
(388, 36, 387, 100, 'Verified', '', 'Document matches trained model class: UR Degree. Description: University of Rwanda Degree Certificate. Confidence: 98.0% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-10 08:02:37', NULL, NULL, 0, NULL, NULL),
(389, 36, 388, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'HASHIMWE Janvier\' (doc ID: 377). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH: Certificate shows \'FOT BAHT ANY\' but candidate is \'SIMBA ALOYS\' — possible borrowed certificate!; MKU QR detected but certificate number not found; QR links to unrecognized domain (-10 penalty)', 'DUPLICATE DOCUMENT: This file was previously submitted by \'HASHIMWE Janvier\'. This is a borrowed certificate. Reject this application.', '2026-06-10 08:04:49', NULL, NULL, 0, NULL, NULL),
(390, 36, 389, 50, 'Suspicious', '⚠ NAME MISMATCH: Certificate shows \'WANENET MENS\' but candidate is \'SIMBA ALOYS\' — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via OCR. Manual review required.', '2026-06-10 08:08:06', NULL, NULL, 0, NULL, NULL),
(391, 22, 390, 100, 'Verified', '', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 97.2% (required 40%). QR verified online at University of Technology and Arts of Byumba. Marked valid at 100%. Candidate may proceed.', '2026-06-10 08:14:53', NULL, NULL, 0, NULL, NULL),
(392, 28, 391, 30, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'IRADUKUNDA Lambert\' (doc ID: 223). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH ONLINE: Name on certificate: \'IRADUKUNDA LAMBERT\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'DUPLICATE DOCUMENT: This file was previously submitted by \'IRADUKUNDA Lambert\'. This is a borrowed certificate. Reject this application.', '2026-06-10 08:15:55', NULL, NULL, 0, NULL, NULL),
(393, 28, 392, 90, 'Verified', '', 'Document matches trained model class: UTAB Degree. Description: University of Technology and Arts of Byumba Degree Certificate. Confidence: 93.0% (required 40%). QR verified online at None. Some issues detected — manual review recommended.', '2026-06-10 08:21:42', NULL, NULL, 0, NULL, NULL),
(394, 28, 393, 0, 'Fake', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'ISAIE NTAWUSIGIMANA\' — DOES NOT MATCH candidate \'JACKY\' — This may be a borrowed certificate!; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-10 08:27:13', NULL, NULL, 0, NULL, NULL),
(395, 31, 394, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 97.1% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-10 08:34:59', NULL, NULL, 0, NULL, NULL),
(396, 31, 395, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 95.2% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-10 08:41:05', NULL, NULL, 0, NULL, NULL),
(397, 31, 396, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 97.1% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-10 09:05:55', '', '', 0, NULL, ''),
(398, 31, 397, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 97.1% (required 40%). QR verified online at Rwanda Polytechnic. Marked valid at 100%. Candidate may proceed.', '2026-06-10 09:12:53', 'https://graduate.rp.ac.rw/?certificate_no=17873', 'Rwanda Polytechnic', 1, 1, 'MUKESHIMANA DELPHINE'),
(399, 31, 398, 100, 'Verified', '', 'Document matches trained model class: RP Degree. Description: Rwanda Polytechnic Degree Certificate. Confidence: 95.2% (required 40%). Marked valid at 100%. Candidate may proceed.', '2026-06-10 09:15:48', 'https://anotinbodirp.ac.rw.:a»SeSnaea?fcAeSa-=a==2BASEL.a..BE»tS/a3', 'Rwanda Polytechnic', 0, NULL, ''),
(400, 31, 399, 50, 'Suspicious', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'CYIZA PATIENT\' — DOES NOT MATCH candidate \'MUKESHIMANA Delphine\' — This may be a borrowed certificate!; ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!', 'Document type confirmed by AI but name mismatch via QR. Manual review required.', '2026-06-10 09:19:56', 'https://graduate.rp.ac.rw/?certificate_no=26136', 'Rwanda Polytechnic', 1, 0, 'CYIZA PATIENT'),
(401, 31, 400, 0, 'Fake', '⚠ CRITICAL: DUPLICATE DOCUMENT DETECTED — This exact file was previously submitted by \'JACKY\' (doc ID: 393). This is a strong indicator of a borrowed or shared certificate!; ⚠ NAME MISMATCH ONLINE: Name on certificate: \'ISAIE NTAWUSIGIMANA\' — DOES NOT MATCH candidate \'MUKESHIMANA Delphine\' — This may be a borrowed certificate!; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!; No trained model document class detected.', 'Document was not recognized by the trained model. Treat as fake or unsupported.', '2026-06-10 09:27:29', 'https://mis.utab.ac.rw/verify.php?degree=UTAB000008886', 'University of Technology and Arts of Byumba', 1, 0, 'ISAIE NTAWUSIGIMANA'),
(402, 31, 401, 30, 'Fake', '⚠ NAME MISMATCH ONLINE: Name on certificate: \'NIYOKWIZERWA JOSELINE\' — DOES NOT MATCH candidate \'MUKESHIMANA Delphine\' — This may be a borrowed certificate!; QR links to unrecognized domain (-10 penalty); ⚠ CRITICAL: Name on certificate does not match candidate — possible borrowed certificate!; ⚠ CRITICAL: Document edited with Adobe Photoshop CC (Windows) — strong indicator of tampering!', 'Document was edited with Adobe Photoshop CC (Windows). This is a strong indicator of tampering. Reject this document.', '2026-06-10 09:33:13', 'https://graduate.rp.ac.rw/?certificate_no=19183', 'Rwanda Polytechnic', 1, 0, 'NIYOKWIZERWA JOSELINE');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `candidates`
--
ALTER TABLE `candidates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `created_by` (`created_by`);

--
-- Indexes for table `documents`
--
ALTER TABLE `documents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `documents_candidate_optional_fk` (`candidate_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `verifications`
--
ALTER TABLE `verifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `document_id` (`document_id`),
  ADD KEY `verifications_candidate_optional_fk` (`candidate_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `candidates`
--
ALTER TABLE `candidates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `documents`
--
ALTER TABLE `documents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=402;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `verifications`
--
ALTER TABLE `verifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=403;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `candidates`
--
ALTER TABLE `candidates`
  ADD CONSTRAINT `candidates_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `documents`
--
ALTER TABLE `documents`
  ADD CONSTRAINT `documents_candidate_optional_fk` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `verifications`
--
ALTER TABLE `verifications`
  ADD CONSTRAINT `verifications_candidate_optional_fk` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `verifications_ibfk_2` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
