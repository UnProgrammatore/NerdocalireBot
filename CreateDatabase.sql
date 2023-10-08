SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

CREATE DATABASE IF NOT EXISTS `nerdocalire` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `nerdocalire`;
CREATE TABLE `nerdocalissiani` (
  `nerdocalissianoId` int(11) NOT NULL,
  `telegramUserId` int(11) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `karma` int(11) NOT NULL DEFAULT 0,
  `telegramUsername` varchar(100) DEFAULT NULL,
  `puntiisacco` bigint(20) NOT NULL DEFAULT 0,
  `canGivePuntiisacco` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `transactions` (
  `transactionId` int(11) NOT NULL,
  `nerdocalissianoId` int(11) NOT NULL,
  `nerdocalire` int(11) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `tdate` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `nerdocalissiani`
  ADD PRIMARY KEY (`nerdocalissianoId`),
  ADD UNIQUE KEY `u_name` (`name`);
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`transactionId`),
  ADD KEY `nerdocalissianoId` (`nerdocalissianoId`);
ALTER TABLE `nerdocalissiani`
  MODIFY `nerdocalissianoId` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `transactions`
  MODIFY `transactionId` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `transactions`
  ADD CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`nerdocalissianoId`) REFERENCES `nerdocalissiani` (`nerdocalissianoId`);
COMMIT;