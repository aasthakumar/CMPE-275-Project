package com.cmpe275.grpcComm;

public class Snippet {
	public static void main(String[] args) {
			JavaClient jc = new JavaClient(args[0],Integer.valueOf(args[1]));
			if(args[2].equalsIgnoreCase("ping")){
				jc.ping("hello");
			}
			else if(args[2].equalsIgnoreCase("get")){
				jc.get(args[3], args[4]);
			}
			else if(args[2].equalsIgnoreCase("put")){
				jc.put(args[3]);
			}		
		}
}

