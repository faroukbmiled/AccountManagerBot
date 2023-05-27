#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <boost/filesystem.hpp>

namespace fs = boost::filesystem;

void processFile(const std::string& filePath, const std::string& keyword, const std::string& outputFileName) {
    std::ifstream inputFile(filePath);

    if (!inputFile) {
        std::cerr << "Error opening input file: " << filePath << '\n';
        return;
    }

    std::ofstream outputFile(outputFileName, std::ios_base::app);

    if (!outputFile) {
        std::cerr << "Error opening output file: " << outputFileName << '\n';
        inputFile.close();
        return;
    }

    std::string line;
    while (std::getline(inputFile, line)) {
        if (line.find(keyword) != std::string::npos) {
            outputFile << line << '\n';
        }
    }

    inputFile.close();
    outputFile.close();
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: program_name keyword\n";
        return 0;
    }

    std::string keyword = argv[1];
    std::string outputFileName = keyword + ".txt";

    std::vector<std::thread> threads;

    fs::directory_iterator end;
    for (fs::directory_iterator file(fs::current_path()); file != end; ++file) {
        if (fs::is_regular_file(file->status()) && file->path().extension() == ".txt") {
            threads.emplace_back(std::thread(processFile, file->path().string(), keyword, outputFileName));
        }
    }

    for (auto& thread : threads) {
        thread.join();
    }

    std::cout << "Processing complete. File has been saved as " << outputFileName << '\n';

    return 0;
}
