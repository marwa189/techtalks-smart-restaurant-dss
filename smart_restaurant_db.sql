-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 05, 2026 at 12:12 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smart_restaurant_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `employee_table`
--

CREATE TABLE `employee_table` (
  `EmployeeID` int(11) NOT NULL,
  `employee_name` varchar(100) NOT NULL,
  `employee_date` date DEFAULT NULL,
  `employee_password` varchar(255) NOT NULL,
  `Role` varchar(50) DEFAULT NULL,
  `last_login` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `inventory_table`
--

CREATE TABLE `inventory_table` (
  `ItemID` int(11) NOT NULL,
  `SupplierID` int(11) DEFAULT NULL,
  `item_name` varchar(100) NOT NULL,
  `production_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `item_count` decimal(10,2) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  `reorder_level` decimal(10,2) DEFAULT NULL,
  `item_cost` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `menu_ingredient_table`
--

CREATE TABLE `menu_ingredient_table` (
  `MenuID` int(11) NOT NULL,
  `ItemID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `menu_table`
--

CREATE TABLE `menu_table` (
  `MenuID` int(11) NOT NULL,
  `menu_item_name` varchar(100) NOT NULL,
  `food_category` varchar(50) DEFAULT NULL,
  `actual_selling_price` decimal(10,2) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recommendation_table`
--

CREATE TABLE `recommendation_table` (
  `RecommendationID` int(11) NOT NULL,
  `MenuID` int(11) DEFAULT NULL,
  `EmployeeID` int(11) DEFAULT NULL,
  `recommendation_date` datetime DEFAULT NULL,
  `recommendation_type` varchar(50) DEFAULT NULL,
  `reason` text DEFAULT NULL,
  `waste_ratio_predicted` decimal(10,4) DEFAULT NULL,
  `adjusted_prep` int(11) DEFAULT NULL,
  `action` enum('DECREASE','INCREASE','KEEP') DEFAULT NULL,
  `weather_condition` enum('Cloudy','Sunny','Rainy','Snowy','Stormy','Windy') DEFAULT NULL,
  `meal_type` varchar(30) DEFAULT NULL,
  `was_followed` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sales_record_table`
--

CREATE TABLE `sales_record_table` (
  `SalesID` int(11) NOT NULL,
  `MenuID` int(11) DEFAULT NULL,
  `EmployeeID` int(11) DEFAULT NULL,
  `quantity_sold` int(11) DEFAULT NULL,
  `sales_date` date DEFAULT NULL,
  `meal_type` varchar(30) DEFAULT NULL,
  `weather_condition` enum('Cloudy','Sunny','Rainy','Snowy','Stormy','Windy') DEFAULT NULL,
  `has_promotion` tinyint(1) DEFAULT NULL,
  `special_event` tinyint(1) DEFAULT NULL,
  `actual_selling_price` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `supplier_table`
--

CREATE TABLE `supplier_table` (
  `SupplierID` int(11) NOT NULL,
  `supplier_name` varchar(100) NOT NULL,
  `supplier_email` varchar(100) DEFAULT NULL,
  `supplier_location` varchar(150) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `waste_record_table`
--

CREATE TABLE `waste_record_table` (
  `WasteID` int(11) NOT NULL,
  `MenuID` int(11) DEFAULT NULL,
  `EmployeeID` int(11) DEFAULT NULL,
  `waste_quantity` decimal(10,2) DEFAULT NULL,
  `waste_date` date DEFAULT NULL,
  `Reason` varchar(255) DEFAULT NULL,
  `meal_type` varchar(30) DEFAULT NULL,
  `weather_condition` enum('Cloudy','Sunny','Rainy','Snowy','Stormy','Windy') DEFAULT NULL,
  `quantity_sold` int(11) DEFAULT NULL,
  `waste_ratio` decimal(10,4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `employee_table`
--
ALTER TABLE `employee_table`
  ADD PRIMARY KEY (`EmployeeID`);

--
-- Indexes for table `inventory_table`
--
ALTER TABLE `inventory_table`
  ADD PRIMARY KEY (`ItemID`),
  ADD KEY `SupplierID` (`SupplierID`);

--
-- Indexes for table `menu_ingredient_table`
--
ALTER TABLE `menu_ingredient_table`
  ADD PRIMARY KEY (`MenuID`,`ItemID`),
  ADD KEY `ItemID` (`ItemID`),
  ADD KEY `MenuID` (`MenuID`);

--
-- Indexes for table `menu_table`
--
ALTER TABLE `menu_table`
  ADD PRIMARY KEY (`MenuID`);

--
-- Indexes for table `recommendation_table`
--
ALTER TABLE `recommendation_table`
  ADD PRIMARY KEY (`RecommendationID`),
  ADD KEY `MenuID` (`MenuID`),
  ADD KEY `EmployeeID` (`EmployeeID`);

--
-- Indexes for table `sales_record_table`
--
ALTER TABLE `sales_record_table`
  ADD PRIMARY KEY (`SalesID`),
  ADD KEY `MenuID` (`MenuID`),
  ADD KEY `EmployeeID` (`EmployeeID`);

--
-- Indexes for table `supplier_table`
--
ALTER TABLE `supplier_table`
  ADD PRIMARY KEY (`SupplierID`),
  ADD KEY `supplier_email` (`supplier_email`);

--
-- Indexes for table `waste_record_table`
--
ALTER TABLE `waste_record_table`
  ADD PRIMARY KEY (`WasteID`),
  ADD KEY `MenuID` (`MenuID`),
  ADD KEY `EmployeeID` (`EmployeeID`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `employee_table`
--
ALTER TABLE `employee_table`
  MODIFY `EmployeeID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `inventory_table`
--
ALTER TABLE `inventory_table`
  MODIFY `ItemID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `menu_table`
--
ALTER TABLE `menu_table`
  MODIFY `MenuID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `recommendation_table`
--
ALTER TABLE `recommendation_table`
  MODIFY `RecommendationID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sales_record_table`
--
ALTER TABLE `sales_record_table`
  MODIFY `SalesID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `supplier_table`
--
ALTER TABLE `supplier_table`
  MODIFY `SupplierID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `waste_record_table`
--
ALTER TABLE `waste_record_table`
  MODIFY `WasteID` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `inventory_table`
--
ALTER TABLE `inventory_table`
  ADD CONSTRAINT `inventory_table_ibfk_1` FOREIGN KEY (`SupplierID`) REFERENCES `supplier_table` (`SupplierID`);

--
-- Constraints for table `menu_ingredient_table`
--
ALTER TABLE `menu_ingredient_table`
  ADD CONSTRAINT `menu_ingredient_table_ibfk_1` FOREIGN KEY (`MenuID`) REFERENCES `menu_table` (`MenuID`),
  ADD CONSTRAINT `menu_ingredient_table_ibfk_2` FOREIGN KEY (`ItemID`) REFERENCES `inventory_table` (`ItemID`);

--
-- Constraints for table `recommendation_table`
--
ALTER TABLE `recommendation_table`
  ADD CONSTRAINT `recommendation_table_ibfk_1` FOREIGN KEY (`MenuID`) REFERENCES `menu_table` (`MenuID`),
  ADD CONSTRAINT `recommendation_table_ibfk_2` FOREIGN KEY (`EmployeeID`) REFERENCES `employee_table` (`EmployeeID`);

--
-- Constraints for table `sales_record_table`
--
ALTER TABLE `sales_record_table`
  ADD CONSTRAINT `sales_record_table_ibfk_1` FOREIGN KEY (`MenuID`) REFERENCES `menu_table` (`MenuID`),
  ADD CONSTRAINT `sales_record_table_ibfk_2` FOREIGN KEY (`EmployeeID`) REFERENCES `employee_table` (`EmployeeID`);

--
-- Constraints for table `waste_record_table`
--
ALTER TABLE `waste_record_table`
  ADD CONSTRAINT `waste_record_table_ibfk_1` FOREIGN KEY (`MenuID`) REFERENCES `menu_table` (`MenuID`),
  ADD CONSTRAINT `waste_record_table_ibfk_2` FOREIGN KEY (`EmployeeID`) REFERENCES `employee_table` (`EmployeeID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
